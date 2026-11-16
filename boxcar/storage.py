"""
Boxcar Image Storage & Local RootFS Cache.
Manages rootfs directories and metadata on disk.
"""

import json
import os
import shutil
import time
from typing import Any, Dict, List, Optional


class ImageStore:
    def __init__(self, base_dir: Optional[str] = None) -> None:
        if base_dir is None:
            base_dir = os.path.expanduser("~/.boxcar/images")
        self.base_dir = os.path.abspath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)

    def _img_key(self, image: str, tag: str = "latest") -> str:
        if ":" in image:
            image, tag = image.split(":", 1)
        safe_name = image.replace("/", "_")
        return f"{safe_name}_{tag}"

    def get_image_dir(self, image: str, tag: str = "latest") -> str:
        return os.path.join(self.base_dir, self._img_key(image, tag))

    def get_rootfs(self, image: str, tag: str = "latest") -> str:
        return os.path.join(self.get_image_dir(image, tag), "rootfs")

    def image_exists(self, image: str, tag: str = "latest") -> bool:
        rootfs = self.get_rootfs(image, tag)
        return os.path.exists(rootfs) and os.path.isdir(rootfs)

    def save_metadata(self, image: str, tag: str, layers: List[str]) -> None:
        img_dir = self.get_image_dir(image, tag)
        rootfs = self.get_rootfs(image, tag)

        # Compute total rootfs size
        total_size = 0
        for dirpath, _, filenames in os.walk(rootfs):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)

        meta = {
            "image": image,
            "tag": tag,
            "layers": layers,
            "size_bytes": total_size,
            "created_at": time.time(),
        }
        with open(os.path.join(img_dir, "metadata.json"), "w") as f:
            json.dump(meta, f, indent=2)

    def list_images(self) -> List[Dict[str, Any]]:
        images = []
        for d in os.listdir(self.base_dir):
            meta_path = os.path.join(self.base_dir, d, "metadata.json")
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, "r") as f:
                        images.append(json.load(f))
                except Exception:
                    pass
        return images

    def delete_image(self, image: str, tag: str = "latest") -> bool:
        img_dir = self.get_image_dir(image, tag)
        if os.path.exists(img_dir):
            shutil.rmtree(img_dir)
            return True
        return False
