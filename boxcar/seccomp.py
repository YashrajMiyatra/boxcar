"""
Seccomp (Secure Computing Mode) Syscall Filtering Subsystem for Boxcar Containers.
Configures OCI linux.seccomp specification to restrict dangerous Linux syscalls (e.g. reboot, kexec_load).
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any


class SeccompFilterSpec:
    """Manages container system call filtering profiles according to OCI runtime-spec."""

    VALID_ACTIONS = {
        "SCMP_ACT_ALLOW",
        "SCMP_ACT_ERRNO",
        "SCMP_ACT_KILL",
        "SCMP_ACT_TRAP",
        "SCMP_ACT_LOG",
    }

    # High-risk syscalls typically blocked by default in secure containers
    DEFAULT_BLOCKED_SYSCALLS = [
        "reboot",
        "kexec_load",
        "kexec_file_load",
        "init_module",
        "finit_module",
        "delete_module",
        "acct",
        "swapon",
        "swapoff",
    ]

    def __init__(
        self,
        default_action: str = "SCMP_ACT_ALLOW",
        architectures: Optional[List[str]] = None,
    ) -> None:
        if default_action not in self.VALID_ACTIONS:
            raise ValueError(f"Invalid default action: {default_action}")
        self.default_action = default_action
        self.architectures = architectures or ["SCMP_ARCH_X86_64", "SCMP_ARCH_AARCH64"]
        self.rules: Dict[str, str] = {}  # syscall_name -> action

        # Apply default blocked syscalls if default is ALLOW
        if self.default_action == "SCMP_ACT_ALLOW":
            for s in self.DEFAULT_BLOCKED_SYSCALLS:
                self.rules[s] = "SCMP_ACT_ERRNO"

    def allow_syscall(self, *names: str) -> None:
        """Explicitly allows system calls."""
        for name in names:
            self.rules[name] = "SCMP_ACT_ALLOW"

    def block_syscall(self, *names: str, action: str = "SCMP_ACT_ERRNO") -> None:
        """Explicitly blocks system calls with specified action."""
        if action not in self.VALID_ACTIONS:
            raise ValueError(f"Invalid action: {action}")
        for name in names:
            self.rules[name] = action

    def evaluate(self, syscall_name: str) -> str:
        """Returns the action to be taken for the given syscall."""
        return self.rules.get(syscall_name, self.default_action)

    def format_oci_spec(self) -> Dict[str, Any]:
        """Formats the profile into OCI linux.seccomp JSON schema."""
        action_groups: Dict[str, List[str]] = {}
        for sc, act in sorted(self.rules.items()):
            action_groups.setdefault(act, []).append(sc)

        syscalls_spec = [
            {"names": names, "action": act}
            for act, names in action_groups.items()
        ]

        return {
            "defaultAction": self.default_action,
            "architectures": list(self.architectures),
            "syscalls": syscalls_spec,
        }
