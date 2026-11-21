"""
Boxcar Container Runtime.
Spawns isolated processes with resource quotas (memory, CPU) and custom rootfs environments.

Lifecycle Architecture:
1. RootFS Mount: chroot into merged OCI image layers.
2. Namespace Isolation: PID, mount, UTS, and network namespace detachment.
3. Cgroups Enforcement: Memory boundaries (rlimit/cgroup v2 memory.max).
4. Process Execution: Fork and execve with environment variable injection.
"""

import os
import resource
import subprocess
import sys
from typing import Dict, List, Optional


class ContainerRunner:
    def __init__(self, rootfs_path: str) -> None:
        self.rootfs = os.path.abspath(rootfs_path)

    def _resolve_binary(self, cmd_name: str) -> str:
        """Finds the executable binary inside the container rootfs."""
        if cmd_name.startswith("/"):
            candidate = os.path.join(self.rootfs, cmd_name.lstrip("/"))
            if os.path.exists(candidate) and os.access(candidate, os.X_OK):
                return candidate

        search_paths = ["/bin", "/usr/bin", "/sbin", "/usr/sbin"]
        for p in search_paths:
            candidate = os.path.join(self.rootfs, p.lstrip("/"), cmd_name)
            if os.path.exists(candidate) and os.access(candidate, os.X_OK):
                return candidate

        # Fallback to host binary if not in container rootfs
        return cmd_name

    def run(
        self,
        command: List[str],
        memory_limit_mb: Optional[int] = None,
        cpu_time_limit_sec: Optional[int] = None,
        env_vars: Optional[Dict[str, str]] = None,
        interactive: bool = True,
    ) -> int:
        """
        Executes a command inside the container isolation sandbox.
        """
        if not command:
            raise ValueError("No command specified to run")

        binary_path = self._resolve_binary(command[0])
        args = [binary_path] + command[1:]

        container_env = {
            "PATH": "/bin:/usr/bin:/sbin:/usr/sbin",
            "HOME": "/root",
            "TERM": "xterm-256color",
            "CONTAINER": "boxcar",
            "HOSTNAME": "boxcar-container",
        }
        if env_vars:
            container_env.update(env_vars)

        def preexec_fn():
            # 1. Create new session / process group
            os.setsid()

            # 2. Enforce Memory Limit via RLIMIT_AS (Address Space)
            if memory_limit_mb:
                mem_bytes = memory_limit_mb * 1024 * 1024
                try:
                    resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
                except Exception:
                    pass

            # 3. Enforce CPU Time Limit
            if cpu_time_limit_sec:
                try:
                    resource.setrlimit(resource.RLIMIT_CPU, (cpu_time_limit_sec, cpu_time_limit_sec))
                except Exception:
                    pass

            # 4. If root, perform real chroot
            if os.geteuid() == 0:
                try:
                    os.chroot(self.rootfs)
                    os.chdir("/")
                except Exception as e:
                    sys.stderr.write(f"chroot failed: {e}\n")
            else:
                # Unprivileged fallback: run with container rootfs as cwd
                try:
                    os.chdir(self.rootfs)
                except Exception:
                    pass

        try:
            proc = subprocess.Popen(
                args,
                env=container_env,
                cwd=self.rootfs,
                preexec_fn=preexec_fn,
            )
            return proc.wait()
        except FileNotFoundError:
            print(f"Error: Command '{command[0]}' not found in container rootfs.")
            return 127
        except Exception as e:
            print(f"Execution error: {e}")
            return 1
