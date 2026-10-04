"""Cost and latency tracking per pipeline execution run."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import time


@dataclass
class StepMetric:
    """Metrics for an individual step or tool call."""

    step_name: str
    latency_ms: float
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0
    cache_hit: bool = False
    details: Optional[str] = None


@dataclass
class RunMetricsTracker:
    """Aggregate metrics collector across a complete run."""

    steps: List[StepMetric] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)

    def record_step(
        self,
        step_name: str,
        latency_ms: float,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost_usd: float = 0.0,
        cache_hit: bool = False,
        details: Optional[str] = None,
    ) -> None:
        self.steps.append(
            StepMetric(
                step_name=step_name,
                latency_ms=latency_ms,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                estimated_cost_usd=cost_usd,
                cache_hit=cache_hit,
                details=details,
            )
        )

    def summary(self) -> Dict[str, float]:
        """Compute aggregate summary stats."""
        total_latency = sum(s.latency_ms for s in self.steps)
        total_in_tokens = sum(s.input_tokens for s in self.steps)
        total_out_tokens = sum(s.output_tokens for s in self.steps)
        total_cost = sum(s.estimated_cost_usd for s in self.steps)
        cache_hits = sum(1 for s in self.steps if s.cache_hit)
        total_steps = len(self.steps)

        return {
            "total_steps": total_steps,
            "cache_hits": cache_hits,
            "cache_hit_ratio": (cache_hits / total_steps) if total_steps else 0.0,
            "total_latency_ms": round(total_latency, 2),
            "total_input_tokens": total_in_tokens,
            "total_output_tokens": total_out_tokens,
            "total_tokens": total_in_tokens + total_out_tokens,
            "total_estimated_cost_usd": round(total_cost, 6),
            "wall_clock_seconds": round(time.time() - self.start_time, 2),
        }


# Global run tracker instance
tracker = RunMetricsTracker()
