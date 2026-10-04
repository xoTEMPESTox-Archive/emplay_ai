"""Hybrid RAG Search Engine combining dense vector search (Chroma) and BM25 with RRF."""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import chromadb
from rank_bm25 import BM25Okapi

from rfp_intelligence.config import settings
from rfp_intelligence.models.domain import (
    DocType,
    DocumentChunk,
    DocumentMetadata,
    SearchQuery,
    SearchResult,
    SourceCitation,
)
from rfp_intelligence.utils.llm import get_embedding, get_embeddings_batch
from rfp_intelligence.utils.logging import get_logger

logger = get_logger("rfp_intelligence.search")


def tokenize_for_bm25(text: str) -> List[str]:
    """Tokenize text into lowercase alphanumeric tokens."""
    return re.findall(r"\b\w+\b", text.lower())


def expand_procurement_query(query_text: str) -> str:
    """Expand domain-specific procurement synonyms to bridge terminology gaps."""
    q_lower = query_text.lower()
    additions = []
    if any(w in q_lower for w in ["deadline", "submission", "due", "closing", "cutoff"]):
        additions.extend(["due date", "closing date", "opening date", "submission deadline"])
    if any(w in q_lower for w in ["addendum", "addendums", "addenda", "amendment"]):
        additions.extend(["addendum", "amendment", "addendum no 2", "extended"])
    if any(w in q_lower for w in ["bond", "deposit", "security"]):
        additions.extend(["bid bond", "cashier check", "security deposit"])
    if any(w in q_lower for w in ["affidavit", "affidavits"]):
        additions.extend(["contract affidavit", "mercury affidavit"])
    if additions:
        return f"{query_text} {' '.join(set(additions))}"
    return query_text


class HybridSearchEngine:
    """Hybrid search engine with vector similarity, BM25, and Reciprocal Rank Fusion."""

    def __init__(self, persist_dir: Optional[Path] = None) -> None:
        self.persist_dir = persist_dir or settings.vector_db_dir
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB persistent client
        self.chroma_client = chromadb.PersistentClient(path=str(self.persist_dir))
        self.collection = self.chroma_client.get_or_create_collection(
            name="rfp_intelligence_chunks",
            metadata={"description": "RFP document chunks and embeddings"},
        )

        # In-memory BM25 structures
        self.bm25_chunks: List[DocumentChunk] = []
        self.bm25_corpus: List[List[str]] = []
        self.bm25_model: Optional[BM25Okapi] = None
        self._load_persisted_bm25()

    def _bm25_cache_path(self) -> Path:
        return self.persist_dir.parent / "bm25_cache.json"

    def _load_persisted_bm25(self) -> None:
        """Load cached BM25 chunks if available on disk, with fallback search and auto-bootstrap."""
        path = self._bm25_cache_path()
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                    self.bm25_chunks = [DocumentChunk(**item) for item in raw_data]
                    self.bm25_corpus = [tokenize_for_bm25(c.text) for c in self.bm25_chunks]
                    if self.bm25_corpus:
                        self.bm25_model = BM25Okapi(self.bm25_corpus)
                logger.info("Loaded %d BM25 chunks from cache", len(self.bm25_chunks))
            except Exception as e:
                logger.warning("Failed to load BM25 cache: %s", e)

        if not self.bm25_chunks:
            # Check alternative repository paths
            alt_candidates = [
                REPO_ROOT / "deliverables" / "source_code" / "data" / "processed" / "bm25_cache.json",
                Path(__file__).resolve().parent.parent.parent.parent / "data" / "processed" / "bm25_cache.json",
            ]
            for ap in alt_candidates:
                if ap.exists() and ap != path:
                    try:
                        with open(ap, "r", encoding="utf-8") as f:
                            raw_data = json.load(f)
                            self.bm25_chunks = [DocumentChunk(**item) for item in raw_data]
                            self.bm25_corpus = [tokenize_for_bm25(c.text) for c in self.bm25_chunks]
                            if self.bm25_corpus:
                                self.bm25_model = BM25Okapi(self.bm25_corpus)
                        logger.info("Loaded %d BM25 chunks from alternative path: %s", len(self.bm25_chunks), ap)
                        self._save_persisted_bm25()
                        break
                    except Exception as e:
                        logger.warning("Failed loading alternative BM25 cache from %s: %s", ap, e)

        # Dynamic bootstrap if still empty
        if not self.bm25_chunks:
            self._auto_bootstrap_default_bids()

    def _auto_bootstrap_default_bids(self) -> None:
        """Auto-ingest default bids into BM25 if cache is missing (e.g. on fresh cloud deployment)."""
        logger.info("Auto-bootstrapping BM25 chunks from assignment data...")
        try:
            from rfp_intelligence.ingestion.parser import IngestionPipeline
            pipeline = IngestionPipeline()
            data_roots = [
                REPO_ROOT / "Assignment-Data-Statements (AI Engineer-Emplay Inc)",
                Path(__file__).resolve().parent.parent.parent.parent.parent / "Assignment-Data-Statements (AI Engineer-Emplay Inc)",
            ]
            target_root = None
            for dr in data_roots:
                if dr.exists():
                    target_root = dr
                    break

            if target_root:
                all_chunks = []
                for bid_name in ["Bid1", "Bid2"]:
                    bp = target_root / bid_name
                    if bp.exists():
                        chunks = pipeline.ingest_bid_folder(bp, bid_id=bid_name)
                        all_chunks.extend(chunks)
                if all_chunks:
                    self.bm25_chunks = all_chunks
                    self.bm25_corpus = [tokenize_for_bm25(c.text) for c in self.bm25_chunks]
                    self.bm25_model = BM25Okapi(self.bm25_corpus)
                    self._save_persisted_bm25()
                    logger.info("Auto-bootstrapped %d chunks into BM25 index", len(self.bm25_chunks))
        except Exception as e:
            logger.warning("Auto-bootstrapping failed: %s", e)

    def _save_persisted_bm25(self) -> None:
        """Save BM25 chunks to disk for persistence across runs."""
        path = self._bm25_cache_path()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump([c.model_dump() for c in self.bm25_chunks], f, indent=2)
        except Exception as e:
            logger.warning("Failed to save BM25 cache: %s", e)

    def get_indexed_bids(self) -> List[str]:
        """Return all unique bid IDs currently indexed in Chroma/BM25."""
        bids = set()
        if self.bm25_chunks:
            for c in self.bm25_chunks:
                if c.metadata.bid_id:
                    bids.add(c.metadata.bid_id)
        if not bids:
            try:
                res = self.collection.get(include=["metadatas"])
                for m in res.get("metadatas", []):
                    if m and "bid_id" in m:
                        bids.add(m["bid_id"])
            except Exception:
                pass
        return sorted(list(bids))

    def get_bid_catalog(self) -> Dict[str, Dict[str, Any]]:
        """Return structured catalog of indexed bids with their files and detected titles."""
        catalog: Dict[str, Dict[str, Any]] = {}
        for b in self.get_indexed_bids():
            catalog[b] = {"files": [], "title": b}

        if self.bm25_chunks:
            for c in self.bm25_chunks:
                bid = c.metadata.bid_id
                if bid in catalog:
                    fn = c.metadata.file_name
                    if fn and fn not in catalog[bid]["files"]:
                        catalog[bid]["files"].append(fn)

        for bid, info in catalog.items():
            files = info["files"]
            title = bid
            for fn in files:
                if "bidnet direct" in fn.lower() or "bid information" in fn.lower():
                    clean_name = fn.split(" - Bid Information")[0].split("__SOURCING")[0].strip()
                    title = clean_name
                    break
                elif "final" in fn.lower() and not title.startswith("Student"):
                    title = fn.replace(".pdf", "").replace("FINAL", "").replace("PORFP", "").replace("_", " ").strip()
            catalog[bid]["title"] = title

        return catalog

    def index_chunks(self, chunks: List[DocumentChunk]) -> int:
        """Incrementally index chunks into Chroma and BM25 without re-indexing duplicates."""
        if not chunks:
            return 0

        existing_ids = set()
        try:
            count = self.collection.count()
            if count > 0:
                existing_res = self.collection.get(include=[])
                existing_ids = set(existing_res.get("ids", []))
        except Exception as e:
            logger.warning("Could not fetch existing IDs from Chroma: %s", e)

        new_chunks = [c for c in chunks if c.chunk_id not in existing_ids]
        if not new_chunks:
            logger.info("All %d chunks already indexed, skipping re-index.", len(chunks))
            return 0

        logger.info("Indexing %d new chunks into Chroma & BM25...", len(new_chunks))

        ids = [c.chunk_id for c in new_chunks]
        documents = [c.text for c in new_chunks]
        metadatas: List[Dict[str, Any]] = []

        for c in new_chunks:
            meta = {
                "bid_id": c.metadata.bid_id,
                "file_name": c.metadata.file_name,
                "doc_type": c.metadata.doc_type.value,
                "page_number": c.metadata.page_number if c.metadata.page_number is not None else -1,
                "addendum_number": c.metadata.addendum_number if c.metadata.addendum_number is not None else -1,
                "is_amendment": c.metadata.is_amendment,
                "is_operative_clause": c.metadata.is_operative_clause,
                "hierarchy_level": c.metadata.hierarchy_level,
            }
            metadatas.append(meta)

        # Batch embed using fast batching
        embeddings = get_embeddings_batch(documents)

        # Upsert into Chroma
        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        # Update BM25
        self.bm25_chunks.extend(new_chunks)
        new_tokenized = [tokenize_for_bm25(c.text) for c in new_chunks]
        self.bm25_corpus.extend(new_tokenized)
        self.bm25_model = BM25Okapi(self.bm25_corpus)
        self._save_persisted_bm25()

        logger.info("Successfully indexed %d chunks (Total Chroma count: %d)", len(new_chunks), self.collection.count())
        return len(new_chunks)

    def _to_search_result(self, chunk_id: str, text: str, meta_dict: Dict[str, Any], score: float) -> SearchResult:
        doc_type_val = meta_dict.get("doc_type", "other")
        doc_type = DocType(doc_type_val) if doc_type_val in DocType._value2member_map_ else DocType.OTHER
        page_no = meta_dict.get("page_number", -1)
        addendum_no = meta_dict.get("addendum_number", -1)

        doc_meta = DocumentMetadata(
            bid_id=meta_dict.get("bid_id", ""),
            file_name=meta_dict.get("file_name", ""),
            doc_type=doc_type,
            page_number=page_no if page_no != -1 else None,
            addendum_number=addendum_no if addendum_no != -1 else None,
            is_amendment=bool(meta_dict.get("is_amendment", False)),
            is_operative_clause=bool(meta_dict.get("is_operative_clause", False)),
            hierarchy_level=int(meta_dict.get("hierarchy_level", 1)),
        )

        snippet = text[:300].strip() + ("..." if len(text) > 300 else "")
        citation = SourceCitation(
            file=doc_meta.file_name,
            page=doc_meta.page_number,
            chunk_id=chunk_id,
            snippet=snippet,
        )

        return SearchResult(
            chunk_id=chunk_id,
            text=text,
            score=round(score, 5),
            citation=citation,
            metadata=doc_meta,
        )

    def _build_where_filter(self, query: SearchQuery) -> Optional[Dict[str, Any]]:
        conditions = []
        if query.bid_id:
            conditions.append({"bid_id": query.bid_id})
        if query.doc_type:
            conditions.append({"doc_type": query.doc_type})

        if not conditions:
            return None
        if len(conditions) == 1:
            return conditions[0]
        return {"$and": conditions}

    def search_vector_only(self, query: SearchQuery) -> List[SearchResult]:
        """Perform dense vector search alone."""
        top_k = query.top_k
        query_text = query.q.strip()
        if not query_text:
            return []

        hits: List[SearchResult] = []
        try:
            query_emb = get_embedding(query_text)
            where_filter = self._build_where_filter(query)

            res = self.collection.query(
                query_embeddings=[query_emb],
                n_results=min(top_k, max(self.collection.count(), 1)),
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )

            if res and res.get("ids") and res["ids"][0]:
                for idx, chunk_id in enumerate(res["ids"][0]):
                    doc = res["documents"][0][idx]
                    meta = res["metadatas"][0][idx]
                    dist = res["distances"][0][idx] if "distances" in res else 0.5
                    score = 1.0 / (1.0 + dist)
                    hits.append(self._to_search_result(chunk_id, doc, meta, score))
        except Exception as e:
            logger.warning("Vector search query error: %s", e)
        return hits

    def search_bm25_only(self, query: SearchQuery) -> List[SearchResult]:
        """Perform BM25 keyword search alone."""
        top_k = query.top_k
        query_text = query.q.strip()
        if not query_text or not self.bm25_model or not self.bm25_chunks:
            return []

        tokens = tokenize_for_bm25(expand_procurement_query(query_text))
        scores = self.bm25_model.get_scores(tokens)
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

        hits: List[SearchResult] = []
        for idx in ranked_indices:
            if scores[idx] <= 0:
                continue
            c = self.bm25_chunks[idx]
            if query.bid_id and c.metadata.bid_id != query.bid_id:
                continue
            if query.doc_type and c.metadata.doc_type.value != query.doc_type:
                continue

            meta_dict = {
                "bid_id": c.metadata.bid_id,
                "file_name": c.metadata.file_name,
                "doc_type": c.metadata.doc_type.value,
                "page_number": c.metadata.page_number if c.metadata.page_number is not None else -1,
                "addendum_number": c.metadata.addendum_number if c.metadata.addendum_number is not None else -1,
            }
            hits.append(self._to_search_result(c.chunk_id, c.text, meta_dict, scores[idx]))
            if len(hits) >= top_k:
                break
        return hits

    def search(self, query: SearchQuery, use_reranker: bool = True) -> List[SearchResult]:
        """Perform hybrid retrieval combining dense vector search and BM25 with RRF."""
        top_k = query.top_k
        query_text = query.q.strip()
        if not query_text:
            return []

        # 1. Dense Vector Search
        vector_hits: List[Dict[str, Any]] = []
        try:
            query_emb = get_embedding(query_text)
            where_filter = self._build_where_filter(query)

            res = self.collection.query(
                query_embeddings=[query_emb],
                n_results=min(top_k * 3, max(self.collection.count(), 1)),
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )

            if res and res.get("ids") and res["ids"][0]:
                for idx, chunk_id in enumerate(res["ids"][0]):
                    doc = res["documents"][0][idx]
                    meta = res["metadatas"][0][idx]
                    dist = res["distances"][0][idx] if "distances" in res else 0.5
                    vector_hits.append(
                        {
                            "chunk_id": chunk_id,
                            "text": doc,
                            "metadata": meta,
                            "distance": dist,
                        }
                    )
        except Exception as e:
            logger.warning("Vector search query error: %s", e)

        # 2. BM25 Lexical Keyword Search
        bm25_hits: List[Dict[str, Any]] = []
        if self.bm25_model and self.bm25_chunks:
            tokens = tokenize_for_bm25(expand_procurement_query(query_text))
            scores = self.bm25_model.get_scores(tokens)
            ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

            for idx in ranked_indices:
                if scores[idx] <= 0:
                    continue
                c = self.bm25_chunks[idx]
                if query.bid_id and c.metadata.bid_id != query.bid_id:
                    continue
                if query.doc_type and c.metadata.doc_type.value != query.doc_type:
                    continue

                bm25_hits.append(
                    {
                        "chunk_id": c.chunk_id,
                        "text": c.text,
                        "metadata": {
                            "bid_id": c.metadata.bid_id,
                            "file_name": c.metadata.file_name,
                            "doc_type": c.metadata.doc_type.value,
                            "page_number": c.metadata.page_number if c.metadata.page_number is not None else -1,
                            "addendum_number": c.metadata.addendum_number if c.metadata.addendum_number is not None else -1,
                        },
                        "bm25_score": scores[idx],
                    }
                )
                if len(bm25_hits) >= top_k * 3:
                    break

        # 3. Reciprocal Rank Fusion (RRF: k=60)
        rrf_scores: Dict[str, float] = {}
        chunk_data: Dict[str, Dict[str, Any]] = {}
        K_RRF = 60.0
        is_amendment_query = any(w in query_text.lower() for w in ["deadline", "due", "date", "addendum", "addenda", "extension", "change", "amendment"])

        for rank, hit in enumerate(vector_hits):
            cid = hit["chunk_id"]
            multiplier = 1.0
            if is_amendment_query and hit["metadata"].get("doc_type") == "addendum":
                multiplier = 1.4
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (multiplier / (K_RRF + rank + 1))
            chunk_data[cid] = hit

        for rank, hit in enumerate(bm25_hits):
            cid = hit["chunk_id"]
            multiplier = 1.2
            if is_amendment_query and hit["metadata"].get("doc_type") == "addendum":
                multiplier = 1.8
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (multiplier / (K_RRF + rank + 1))
            if cid not in chunk_data:
                chunk_data[cid] = hit

        # 4. Optional Reranking (Term overlap & keyword density scoring)
        final_scored: List[tuple[str, float]] = []
        query_terms = set(tokenize_for_bm25(query_text))

        for cid, rrf_score in rrf_scores.items():
            score = rrf_score
            if use_reranker:
                text_lower = chunk_data[cid]["text"].lower()
                matches = sum(1 for term in query_terms if term in text_lower)
                overlap_ratio = matches / len(query_terms) if query_terms else 0
                score = rrf_score * (1.0 + overlap_ratio)
            final_scored.append((cid, score))

        final_scored.sort(key=lambda x: x[1], reverse=True)

        # 5. Format SearchResult items
        results: List[SearchResult] = []
        for cid, score in final_scored[:top_k]:
            data = chunk_data[cid]
            results.append(self._to_search_result(cid, data["text"], data["metadata"], score))

        return results

    def multi_query_search(
        self,
        question: str,
        bid_id: Optional[str] = None,
        top_k: int = 6,
        use_reranker: bool = True,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> Tuple[List[SearchResult], Any]:
        """Execute multi-query search with balanced multi-bid partitioning for comparative queries."""
        from rfp_intelligence.search.decomposition import decompose_query

        catalog = self.get_bid_catalog()
        decomposed = decompose_query(question, catalog=catalog, model=model, api_key=api_key)

        # Determine target scope
        target_bids = [bid_id] if bid_id else decomposed.target_bids
        is_comparative = decomposed.is_comparative and len(target_bids) > 1

        all_hits_by_chunk: Dict[str, SearchResult] = {}
        rrf_scores: Dict[str, float] = {}
        K_RRF = 60.0

        if is_comparative:
            # Balanced retrieval across each target bid partition
            k_per_bid = max(3, top_k // len(target_bids))
            for b in target_bids:
                for sub_q in decomposed.sub_queries:
                    sq = SearchQuery(q=sub_q, bid_id=b, top_k=k_per_bid * 2)
                    hits = self.search(sq, use_reranker=use_reranker)
                    for rank, hit in enumerate(hits):
                        cid = hit.chunk_id
                        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (K_RRF + rank + 1))
                        if cid not in all_hits_by_chunk:
                            all_hits_by_chunk[cid] = hit

            # Ensure each target bid gets guaranteed representation in the final candidate list
            bid_partitions: Dict[str, List[tuple[str, float]]] = {b: [] for b in target_bids}
            for cid, score in rrf_scores.items():
                b = all_hits_by_chunk[cid].metadata.bid_id
                if b in bid_partitions:
                    bid_partitions[b].append((cid, score))

            final_results = []
            for b in target_bids:
                bid_partitions[b].sort(key=lambda x: x[1], reverse=True)
                for cid, score in bid_partitions[b][:k_per_bid]:
                    res = all_hits_by_chunk[cid]
                    res.score = round(score, 5)
                    final_results.append(res)
            return final_results, decomposed
        else:
            # Single-bid or general search across all bids
            active_bid = target_bids[0] if (target_bids and len(target_bids) == 1) else None
            for sub_q in decomposed.sub_queries:
                sq = SearchQuery(q=sub_q, bid_id=active_bid, top_k=top_k * 2)
                hits = self.search(sq, use_reranker=use_reranker)
                for rank, hit in enumerate(hits):
                    cid = hit.chunk_id
                    rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (K_RRF + rank + 1))
                    if cid not in all_hits_by_chunk:
                        all_hits_by_chunk[cid] = hit

            ranked_cids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)
            final_results = []
            for cid in ranked_cids[:top_k]:
                res = all_hits_by_chunk[cid]
                res.score = round(rrf_scores[cid], 5)
                final_results.append(res)

            return final_results, decomposed


def rerank_passages_listwise(
    question: str,
    candidates: List[SearchResult],
    top_k: int = 4,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
) -> List[SearchResult]:
    """Use LiteLLM to perform listwise ranking and select the most relevant evidentiary chunks."""
    if len(candidates) <= top_k:
        return candidates

    prompt_items = []
    for idx, c in enumerate(candidates):
        snippet = c.text[:250].replace("\n", " ")
        prompt_items.append(f"[{idx}] [Bid: {c.metadata.bid_id} | File: {c.citation.file} | Page {c.citation.page}]: {snippet}")

    prompt = (
        f"Question: {question}\n\n"
        "Candidate document passages across bids:\n"
        + "\n".join(prompt_items)
        + f"\n\nSelect the top indices of the passages that directly answer or provide essential legal/factual evidence for the question.\n"
        + "If comparing bids, select representative evidence for EACH bid.\n"
        + f"Return a JSON object with a 'ranked_indices' array of up to {top_k} integers in order of relevance, e.g. {{\"ranked_indices\": [0, 2, 1]}}."
    )

    try:
        from rfp_intelligence.utils.llm import get_completion

        resp = get_completion(
            prompt=prompt,
            system_prompt="You are an expert information retrieval reranker. Output JSON object only.",
            model=model,
            api_key=api_key,
            json_mode=True,
            timeout=15,
        )
        parsed = json.loads(resp)
        selected_indices = parsed.get("ranked_indices", parsed) if isinstance(parsed, dict) else parsed
        if isinstance(selected_indices, list):
            ranked = [candidates[i] for i in selected_indices if isinstance(i, int) and 0 <= i < len(candidates)]
            if ranked:
                for c in candidates:
                    if c not in ranked and len(ranked) < top_k:
                        ranked.append(c)
                return ranked[:top_k]
    except Exception as e:
        logger.warning("Listwise reranking failed, falling back to RRF order: %s", e)

    return candidates[:top_k]

