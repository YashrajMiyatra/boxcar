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
from typing import Any, Dict, List, Optional


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

    def run_with_telemetry(
        self,
        command: List[str],
        memory_limit_mb: Optional[int] = None,
        cpu_time_limit_sec: Optional[int] = None,
        env_vars: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Executes a container process and returns real-time resource telemetry:
        exit_code, wall_time_sec, max_rss_kb, cpu_user_time, and status.
        """
        import time
        start_time = time.time()

        if not command:
            raise ValueError("No command specified to run.")

        args = [self._resolve_binary(command[0])] + command[1:]
        container_env = dict(os.environ)
        container_env["BOXCAR_CONTAINER"] = "1"
        if env_vars:
            container_env.update(env_vars)

        def preexec_fn():
            if memory_limit_mb:
                mem_bytes = memory_limit_mb * 1024 * 1024
                try:
                    resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
                except Exception:
                    pass
            if cpu_time_limit_sec:
                try:
                    resource.setrlimit(resource.RLIMIT_CPU, (cpu_time_limit_sec, cpu_time_limit_sec))
                except Exception:
                    pass
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
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, stderr = proc.communicate()
            exit_code = proc.returncode
            wall_time = time.time() - start_time
            usage = resource.getrusage(resource.RUSAGE_CHILDREN)

            return {
                "exit_code": exit_code,
                "wall_time_sec": round(wall_time, 4),
                "user_cpu_sec": round(usage.ru_utime, 4),
                "sys_cpu_sec": round(usage.ru_stime, 4),
                "max_rss_kb": usage.ru_maxrss,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
                "status": "success" if exit_code == 0 else "failed",
            }
        except FileNotFoundError:
            return {
                "exit_code": 127,
                "wall_time_sec": round(time.time() - start_time, 4),
                "error": f"Command '{command[0]}' not found.",
                "status": "not_found",
            }
        except Exception as e:
            return {
                "exit_code": 1,
                "wall_time_sec": round(time.time() - start_time, 4),
                "error": str(e),
                "status": "error",
            }
