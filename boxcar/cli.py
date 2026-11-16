"""
Boxcar CLI: The Lightweight Container Engine.
Pull OCI images from Docker Hub, enforce cgroup/resource limits, and run containers.
"""

import argparse
import os
import sys
from .registry import DockerRegistryClient
from .storage import ImageStore
from .runtime import ContainerRunner


def format_bytes(num: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f} {unit}"
        num /= 1024.0
    return f"{num:.1f} TB"


def cmd_pull(store: ImageStore, client: DockerRegistryClient, image: str) -> None:
    tag = "latest"
    if ":" in image:
        image, tag = image.split(":", 1)

    print(f"\033[1;36m[*] Pulling '{image}:{tag}' from Docker Hub...\033[0m")
    rootfs = store.get_rootfs(image, tag)

    def on_progress(msg: str):
        print(f"  \033[90m-> {msg}\033[0m")

    try:
        layers = client.pull_image(image, tag, rootfs, progress_callback=on_progress)
        store.save_metadata(image, tag, layers)
        print(f"\033[1;32m[+] Successfully pulled and extracted '{image}:{tag}'\033[0m\n")
    except Exception as e:
        print(f"\033[1;31mError pulling image: {e}\033[0m")
        sys.exit(1)


def cmd_images(store: ImageStore) -> None:
    images = store.list_images()
    if not images:
        print("No container images found locally. Run: boxcar pull <image>")
        return

    print(f"\033[1m{'REPOSITORY':<25} {'TAG':<12} {'IMAGE ID':<15} {'SIZE':<12}\033[0m")
    print("-" * 65)
    for img in images:
        repo = img.get("image", "unknown")
        tag = img.get("tag", "latest")
        first_layer = img.get("layers", ["unknown"])[0].split(":")[-1][:12]
        size = format_bytes(img.get("size_bytes", 0))
        print(f"{repo:<25} {tag:<12} {first_layer:<15} {size:<12}")


def cmd_run(store: ImageStore, client: DockerRegistryClient, args: argparse.Namespace) -> None:
    image = args.image
    tag = "latest"
    if ":" in image:
        image, tag = image.split(":", 1)

    # Auto-pull if image not present
    if not store.image_exists(image, tag):
        print(f"[*] Image '{image}:{tag}' not found locally. Initiating pull...")
        cmd_pull(store, client, f"{image}:{tag}")

    rootfs = store.get_rootfs(image, tag)
    runner = ContainerRunner(rootfs)

    command = args.cmd
    if not command:
        command = ["/bin/sh"]

    print(f"\033[1;34m[*] Running container from '{image}:{tag}'...\033[0m")
    if args.memory:
        print(f"  \033[90mMemory limit: {args.memory} MB\033[0m")

    exit_code = runner.run(command, memory_limit_mb=args.memory, cpu_time_limit_sec=args.cpu)
    sys.exit(exit_code)


def cmd_rmi(store: ImageStore, image: str) -> None:
    tag = "latest"
    if ":" in image:
        image, tag = image.split(":", 1)
    if store.delete_image(image, tag):
        print(f"\033[1;32m[+] Deleted image '{image}:{tag}'\033[0m")
    else:
        print(f"\033[1;31mError: Image '{image}:{tag}' not found.\033[0m")


def main() -> None:
    parser = argparse.ArgumentParser(description="Boxcar: Minimalist Container Runtime & Docker Puller")
    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # pull
    p_pull = subparsers.add_parser("pull", help="Pull an image from Docker Hub")
    p_pull.add_argument("image", help="Image name (e.g. alpine, busybox, ubuntu)")

    # images
    subparsers.add_parser("images", help="List locally downloaded images")

    # run
    p_run = subparsers.add_parser("run", help="Run a command inside a container")
    p_run.add_argument("-m", "--memory", type=int, help="Memory limit in megabytes")
    p_run.add_argument("--cpu", type=int, help="CPU time limit in seconds")
    p_run.add_argument("image", help="Image name (e.g. alpine)")
    p_run.add_argument("cmd", nargs=argparse.REMAINDER, help="Command to execute")

    # rmi
    p_rmi = subparsers.add_parser("rmi", help="Remove an image")
    p_rmi.add_argument("image", help="Image name to remove")

    args = parser.parse_args()

    store = ImageStore()
    client = DockerRegistryClient()

    if args.subcommand == "pull":
        cmd_pull(store, client, args.image)
    elif args.subcommand == "images":
        cmd_images(store)
    elif args.subcommand == "run":
        cmd_run(store, client, args)
    elif args.subcommand == "rmi":
        cmd_rmi(store, args.image)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
