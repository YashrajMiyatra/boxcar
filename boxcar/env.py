"""
Container Environment Variable Injection Subsystem for Boxcar.
Parses CLI key-value pairs (-e KEY=VAL), host environment inheritances (-e KEY),
and dotenv environment files.
"""

from __future__ import annotations
import os
from typing import Dict, List, Optional


class EnvironmentInjector:
    """Manages environment variable resolution and merging for container runtime."""

    def __init__(self, base_env: Optional[Dict[str, str]] = None) -> None:
        self.env: Dict[str, str] = dict(base_env) if base_env else {}

    def inject_pair(self, spec: str, host_lookup: bool = True) -> None:
        """
        Parses a single spec:
        - 'KEY=VAL': Sets KEY to VAL.
        - 'KEY': If host_lookup=True, retrieves value from host os.environ.
        """
        spec = spec.strip()
        if not spec:
            return
        if "=" in spec:
            k, v = spec.split("=", 1)
            self.env[k.strip()] = v
        else:
            k = spec
            if host_lookup and k in os.environ:
                self.env[k] = os.environ[k]
            else:
                self.env[k] = ""

    def inject_pairs(self, specs: List[str]) -> None:
        for s in specs:
            self.inject_pair(s)

    def load_env_file(self, file_content: str) -> None:
        """Parses a multi-line dotenv file format."""
        for line in file_content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            self.inject_pair(line, host_lookup=False)

    def to_env_list(self) -> List[str]:
        """Returns list of 'KEY=VAL' strings for execve / OCI process spec."""
        return [f"{k}={v}" for k, v in sorted(self.env.items())]
