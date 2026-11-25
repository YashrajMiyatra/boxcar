"""
OOM Score Adjustment Subsystem for Boxcar Containers.
Configures /proc/[pid]/oom_score_adj to tune Linux kernel Out-Of-Memory killer priority.
"""

from __future__ import annotations
import os
from typing import Dict, Any


class OOMScoreAdjustSpec:
    """Specification and applicator for container process oom_score_adj."""

    MIN_SCORE = -1000
    MAX_SCORE = 1000

    def __init__(self, score: int = 0) -> None:
        self.score = self._validate_score(score)

    @classmethod
    def _validate_score(cls, score: int) -> int:
        if not isinstance(score, int):
            raise TypeError(f"oom_score_adj must be an integer, got {type(score).__name__}")
        if not (cls.MIN_SCORE <= score <= cls.MAX_SCORE):
            raise ValueError(
                f"oom_score_adj {score} is out of bounds [{cls.MIN_SCORE}, {cls.MAX_SCORE}]"
            )
        return score

    def write_to_proc(self, pid: int, proc_root: str = "/proc") -> None:
        """Writes the score to /proc/<pid>/oom_score_adj."""
        target_path = os.path.join(proc_root, str(pid), "oom_score_adj")
        with open(target_path, "w") as f:
            f.write(f"{self.score}\n")

    def format_oci_spec(self) -> Dict[str, Any]:
        """Returns standard OCI process oomScoreAdj dictionary."""
        return {"oomScoreAdj": self.score}
