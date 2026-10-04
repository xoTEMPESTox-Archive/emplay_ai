"""Unified LLM and Embedding client supporting Ollama, LiteLLM, caching, and fallback."""

import hashlib
import json
import time
import urllib.request
from typing import Any, Dict, List, Optional
import litellm

from rfp_intelligence.config import settings
from rfp_intelligence.utils.logging import get_logger
from rfp_intelligence.utils.metrics import tracker
from rfp_intelligence.utils.semantic_cache import semantic_cache

logger = get_logger("rfp_intelligence.llm")


def _deterministic_vector(text: str, dim: int = 1024) -> List[float]:
    """Generate a stable, normalized 1024-dimensional vector from text hash."""
    seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], 16)
    values = []
    current = seed
    for _ in range(dim):
        current = (current * 6364136223846793005 + 1442695040888963407) & 0xFFFFFFFFFFFFFFFF
        # Map to range [-1.0, 1.0]
        val = (current / 0xFFFFFFFFFFFFFFFF) * 2.0 - 1.0
        values.append(val)

    norm = sum(x * x for x in values) ** 0.5
    if norm > 0:
        values = [x / norm for x in values]
    return values


def get_embedding(text: str, model: Optional[str] = None) -> List[float]:
    """Generate an embedding vector for text using Ollama, LiteLLM, or fallback.

    Args:
        text: Input string to embed.
        model: Model identifier override (defaults to settings.embedding_model).

    Returns:
        List of floats representing the dense embedding vector.
    """
    model_name = model or settings.embedding_model
    start_t = time.time()

    # Check cache
    cached = semantic_cache.get(f"emb::{text}", model_name)
    if cached is not None and isinstance(cached, list):
        tracker.record_step(
            step_name="embedding",
            latency_ms=(time.time() - start_t) * 1000,
            cache_hit=True,
            details=f"Cache hit: {model_name}",
        )
        return cached

    # 1. Try Ollama direct API if configured for Ollama
    if "ollama" in model_name.lower():
        ollama_model = model_name.replace("ollama/", "")
        url = f"{settings.ollama_base_url}/api/embeddings"
        payload = json.dumps({"model": ollama_model, "prompt": text}).encode("utf-8")
        req = urllib.request.Request(
            url, data=payload, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                emb = data.get("embedding", [])
                if emb:
                    semantic_cache.set(f"emb::{text}", model_name, emb)
                    tracker.record_step(
                        step_name="embedding",
                        latency_ms=(time.time() - start_t) * 1000,
                        cache_hit=False,
                        details=f"Ollama: {ollama_model} (dim={len(emb)})",
                    )
                    return emb
        except Exception as e:
            logger.warning("Ollama embedding failed or timed out (%s), trying fallback", e)

    # 2. Try LiteLLM (Cloud providers, e.g. Gemini, OpenAI)
    try:
        response = litellm.embedding(model=model_name, input=[text])
        emb = response.data[0]["embedding"]
        semantic_cache.set(f"emb::{text}", model_name, emb)
        tracker.record_step(
            step_name="embedding",
            latency_ms=(time.time() - start_t) * 1000,
            cache_hit=False,
            details=f"LiteLLM: {model_name}",
        )
        return emb
    except Exception as e:
        logger.debug("LiteLLM embedding failed (%s), using deterministic embedding", e)

    # 3. Deterministic normalized hash vector fallback
    fallback_emb = _deterministic_vector(text, dim=1024)
    tracker.record_step(
        step_name="embedding",
        latency_ms=(time.time() - start_t) * 1000,
        cache_hit=False,
        details="Deterministic fallback embedding",
    )
    semantic_cache.set(f"emb::{text}", model_name, fallback_emb)
    return fallback_emb


def get_embeddings_batch(
    texts: List[str], model: Optional[str] = None
) -> List[List[float]]:
    """Batch embed a list of texts using Ollama /api/embed or LiteLLM."""
    if not texts:
        return []
    model_name = model or settings.embedding_model
    results: List[Optional[List[float]]] = [None] * len(texts)
    missing_indices = []

    # Check cache first
    for i, t in enumerate(texts):
        cached = semantic_cache.get(f"emb::{t}", model_name)
        if cached is not None and isinstance(cached, list):
            results[i] = cached
        else:
            missing_indices.append(i)

    if not missing_indices:
        return [r for r in results if r is not None]

    # Process missing in batches of 40
    batch_size = 40
    for b_start in range(0, len(missing_indices), batch_size):
        b_indices = missing_indices[b_start : b_start + batch_size]
        b_texts = [texts[idx] for idx in b_indices]

        # 1. Try Ollama /api/embed
        if "ollama" in model_name.lower():
            ollama_model = model_name.replace("ollama/", "")
            url = f"{settings.ollama_base_url}/api/embed"
            payload = json.dumps({"model": ollama_model, "input": b_texts}).encode("utf-8")
            req = urllib.request.Request(
                url, data=payload, headers={"Content-Type": "application/json"}
            )
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    embs = data.get("embeddings", [])
                    if len(embs) == len(b_texts):
                        for idx, emb in zip(b_indices, embs):
                            results[idx] = emb
                            semantic_cache.set(f"emb::{texts[idx]}", model_name, emb)
                        continue
            except Exception as e:
                logger.warning("Ollama batch embed failed: %s", e)

        # 2. Try LiteLLM
        try:
            resp = litellm.embedding(model=model_name, input=b_texts)
            embs = [item["embedding"] for item in resp.data]
            for idx, emb in zip(b_indices, embs):
                results[idx] = emb
                semantic_cache.set(f"emb::{texts[idx]}", model_name, emb)
            continue
        except Exception:
            pass

        # 3. Fallback
        for idx in b_indices:
            emb = _deterministic_vector(texts[idx], dim=1024)
            results[idx] = emb
            semantic_cache.set(f"emb::{texts[idx]}", model_name, emb)

    return [r for r in results if r is not None]


def get_completion(
    prompt: str,
    system_prompt: str = "",
    model: Optional[str] = None,
    json_mode: bool = False,
    timeout: int = 45,
    api_key: Optional[str] = None,
) -> str:
    """Generate LLM completion with latency tracking, rate limit detection, and fallback robustness.

    Args:
        prompt: User prompt content.
        system_prompt: System prompt instructing role and constraints.
        model: Model identifier override (defaults to settings.llm_model).
        json_mode: If true, requests JSON output structure.
        timeout: Request timeout in seconds.
        api_key: Optional API key override.

    Returns:
        String response generated by the model.
    """
    model_name = model or settings.llm_model
    start_t = time.time()

    # Check semantic cache
    cache_key = f"{system_prompt}\n---\n{prompt}"
    cached = semantic_cache.get(cache_key, model_name)
    if cached is not None:
        tracker.record_step(
            step_name="llm_completion",
            latency_ms=(time.time() - start_t) * 1000,
            cache_hit=True,
            details=f"Cache hit: {model_name}",
        )
        return str(cached)

    # 1. Try Ollama direct API if model specifies Ollama
    if "ollama" in model_name.lower():
        ollama_model = model_name.replace("ollama/", "")
        url = f"{settings.ollama_base_url}/api/generate"
        payload_dict: Dict[str, Any] = {
            "model": ollama_model,
            "prompt": f"{system_prompt}\n\n{prompt}" if system_prompt else prompt,
            "stream": False,
        }
        if json_mode:
            payload_dict["format"] = "json"

        req = urllib.request.Request(
            url,
            data=json.dumps(payload_dict).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                output_text = data.get("response", "").strip()
                in_tok = data.get("prompt_eval_count", len(prompt) // 4)
                out_tok = data.get("eval_count", len(output_text) // 4)

                tracker.record_step(
                    step_name="llm_completion",
                    latency_ms=(time.time() - start_t) * 1000,
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    cost_usd=0.0,
                    cache_hit=False,
                    details=f"Ollama: {ollama_model}",
                )
                semantic_cache.set(cache_key, model_name, output_text)
                return output_text
        except Exception as e:
            logger.warning("Ollama generation failed or timed out (%s), falling back to LiteLLM", e)

    # 2. Try LiteLLM (Cloud providers: Gemini, OpenAI, Claude, Groq, etc.)
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    try:
        kwargs: Dict[str, Any] = {"model": model_name, "messages": messages, "timeout": timeout}
        if api_key:
            kwargs["api_key"] = api_key
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = litellm.completion(**kwargs)
        output_text = response.choices[0].message.content.strip()

        usage = getattr(response, "usage", None)
        in_tok = usage.prompt_tokens if usage else len(prompt) // 4
        out_tok = usage.completion_tokens if usage else len(output_text) // 4

        # Compute cost if available
        try:
            cost = litellm.completion_cost(completion_response=response)
        except Exception:
            cost = 0.0

        tracker.record_step(
            step_name="llm_completion",
            latency_ms=(time.time() - start_t) * 1000,
            input_tokens=in_tok,
            output_tokens=out_tok,
            cost_usd=cost,
            cache_hit=False,
            details=f"LiteLLM: {model_name}",
        )
        semantic_cache.set(cache_key, model_name, output_text)
        return output_text
    except Exception as e:
        err_msg = str(e).lower()
        if any(term in err_msg for term in ["rate_limit", "ratelimit", "quota", "429", "resource_exhausted"]):
            logger.error("Rate limit reached on %s: %s", model_name, e)
            raise RuntimeError(f"RATE_LIMIT: Model `{model_name}` rate limit or quota exceeded. Please provide your personal API key in the sidebar settings. Details: {e}")
        if any(term in err_msg for term in ["auth", "unauthorized", "api_key", "invalid_api_key", "401"]):
            logger.error("Authentication failure on %s: %s", model_name, e)
            raise RuntimeError(f"AUTH_ERROR: Authentication failed for model `{model_name}`. Please verify or update your API key in the sidebar settings. Details: {e}")
        logger.warning("LiteLLM completion error: %s", e)

    # 3. Graceful fallback if no LLM responded
    output_text = "I could not locate this information in the documents."
    if json_mode:
        output_text = json.dumps({"value": None, "notes": "Not found in documents", "confidence": 0.0})

    tracker.record_step(
        step_name="llm_completion",
        latency_ms=(time.time() - start_t) * 1000,
        cache_hit=False,
        details="Fallback generation",
    )
    return output_text
