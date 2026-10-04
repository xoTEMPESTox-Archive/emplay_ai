"""Semantic cache for caching repeated queries and LLM outputs."""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional
from rfp_intelligence.config import REPO_ROOT, settings


class SemanticCache:
    """Cache for repeated queries and LLM prompts using content hashing."""

    def __init__(self, cache_file: Optional[Path] = None) -> None:
        self.cache_file = (
            cache_file
            or REPO_ROOT
            / "deliverables"
            / "source_code"
            / "data"
            / "processed"
            / "semantic_cache.json"
        )
        self._memory_cache: Dict[str, Any] = {}
        self._load_cache()

    def _hash_key(self, prompt: str, model: str) -> str:
        content = f"{model}::{prompt.strip()}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _load_cache(self) -> None:
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self._memory_cache = json.load(f)
            except Exception:
                self._memory_cache = {}

    def _save_cache(self) -> None:
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self._memory_cache, f, indent=2)
        except Exception:
            pass

    def get(self, prompt: str, model: str) -> Optional[Any]:
        """Retrieve cached result if caching is enabled."""
        if not settings.enable_semantic_cache:
            return None
        key = self._hash_key(prompt, model)
        return self._memory_cache.get(key)

    def set(self, prompt: str, model: str, value: Any) -> None:
        """Store result in cache."""
        if not settings.enable_semantic_cache:
            return
        key = self._hash_key(prompt, model)
        self._memory_cache[key] = value
        self._save_cache()

    def clear(self) -> None:
        """Clear the cache."""
        self._memory_cache.clear()
        if self.cache_file.exists():
            try:
                self.cache_file.unlink()
            except Exception:
                pass


# Global singleton instance
semantic_cache = SemanticCache()
