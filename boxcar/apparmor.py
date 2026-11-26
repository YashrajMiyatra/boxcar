"""
AppArmor Security Subsystem for Boxcar.
Generates, validates, and manages AppArmor MAC (Mandatory Access Control) profiles
for Linux container process isolation complying with OCI Runtime Spec process.apparmorProfile.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class AppArmorRule:
    path: str
    permissions: str
    deny: bool = False

    def to_profile_line(self) -> str:
        prefix = "deny " if self.deny else ""
        return f"  {prefix}{self.path} {self.permissions},"


class AppArmorProfileSpec:
    """Manages Linux container AppArmor confinement profiles."""

    DEFAULT_PROFILE_NAME = "boxcar-default"

    def __init__(
        self,
        name: str = DEFAULT_PROFILE_NAME,
        mode: str = "enforce",
        rules: Optional[List[AppArmorRule]] = None,
    ) -> None:
        if mode not in ("enforce", "complain", "disabled"):
            raise ValueError(f"Invalid AppArmor mode '{mode}', must be enforce, complain, or disabled")
        self.name = name.strip()
        if not self.name:
            raise ValueError("AppArmor profile name cannot be empty")
        self.mode = mode
        self.rules: List[AppArmorRule] = list(rules or [])

    def add_rule(self, path: str, permissions: str, deny: bool = False) -> None:
        """Adds a path permission rule (e.g. path='/proc/sys/**', permissions='wklx', deny=True)."""
        if not path or not permissions:
            raise ValueError("Path and permissions must not be empty")
        self.rules.append(AppArmorRule(path=path, permissions=permissions, deny=deny))

    def generate_profile_text(self) -> str:
        """Generates valid AppArmor profile definition text."""
        flags = "flags=(attach_disconnected,mediate_deleted)"
        if self.mode == "complain":
            flags = "flags=(complain,attach_disconnected,mediate_deleted)"

        lines = [
            "#include <tunables/global>",
            "",
            f"profile {self.name} {flags} {{",
            "  #include <abstractions/base>",
            "  network,",
            "  capability,",
            "  file,",
        ]
        for rule in self.rules:
            lines.append(rule.to_profile_line())
        lines.append("}")
        return "\n".join(lines)

    def format_oci_spec(self) -> Dict[str, Any]:
        """Returns standard OCI process configuration with apparmorProfile."""
        if self.mode == "disabled":
            return {"process": {"apparmorProfile": "unconfined"}}
        return {"process": {"apparmorProfile": self.name}}

    @classmethod
    def create_default_profile(cls, name: str = DEFAULT_PROFILE_NAME) -> AppArmorProfileSpec:
        """Creates standard secure container AppArmor profile denying dangerous kernel writes."""
        spec = cls(name=name, mode="enforce")
        spec.add_rule(path="/proc/sys/**", permissions="wklx", deny=True)
        spec.add_rule(path="/proc/sysrq-trigger", permissions="rwklx", deny=True)
        spec.add_rule(path="/proc/kcore", permissions="rwklx", deny=True)
        spec.add_rule(path="/sys/**", permissions="wklx", deny=True)
        spec.add_rule(path="/sys/firmware/**", permissions="rwklx", deny=True)
        return spec
