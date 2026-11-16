"""
Docker Registry v2 Client.
Fetches real OCI container images and layer tarballs directly from Docker Hub.
Zero external dependencies required (uses standard library urllib).
"""

import json
import os
import tarfile
import urllib.request
from typing import Callable, List, Optional, Tuple


class DockerRegistryClient:
    AUTH_URL = "https://auth.docker.io/token"
    REGISTRY_URL = "https://registry-1.docker.io/v2"

    def __init__(self) -> None:
        pass

    def _get_auth_token(self, repository: str) -> str:
        """Obtains an anonymous pull bearer token from Docker Hub auth service."""
        if "/" not in repository:
            repo_name = f"library/{repository}"
        else:
            repo_name = repository

        url = f"{self.AUTH_URL}?service=registry.docker.io&scope=repository:{repo_name}:pull"
        req = urllib.request.Request(url, headers={"User-Agent": "Boxcar/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["token"]

    def pull_image(
        self,
        image_name: str,
        tag: str = "latest",
        destination_dir: str = "",
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> List[str]:
        """
        Pulls all layers for image_name:tag and unpacks them into destination_dir.
        Returns list of layer digest hashes.
        """
        if ":" in image_name:
            image_name, tag = image_name.split(":", 1)

        repo = f"library/{image_name}" if "/" not in image_name else image_name
        token = self._get_auth_token(image_name)

        # 1. Fetch Image Manifest
        manifest_url = f"{self.REGISTRY_URL}/{repo}/manifests/{tag}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.docker.distribution.manifest.v2+json, application/vnd.oci.image.manifest.v1+json",
            "User-Agent": "Boxcar/1.0",
        }

        req = urllib.request.Request(manifest_url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            manifest = json.loads(resp.read().decode("utf-8"))

        layers = manifest.get("layers", [])
        if not layers and "fsLayers" in manifest:
            # v1 fallback
            layers = [{"digest": l["blobSum"]} for l in manifest["fsLayers"]]

        os.makedirs(destination_dir, exist_ok=True)
        downloaded_digests = []

        # 2. Download and unpack each layer
        for idx, layer in enumerate(layers, 1):
            digest = layer["digest"]
            downloaded_digests.append(digest)
            short_digest = digest.split(":")[-1][:12]

            if progress_callback:
                progress_callback(f"Pulling layer {idx}/{len(layers)}: {short_digest}")

            blob_url = f"{self.REGISTRY_URL}/{repo}/blobs/{digest}"
            blob_req = urllib.request.Request(blob_url, headers={"Authorization": f"Bearer {token}"})

            # Stream download layer
            temp_tar = os.path.join(destination_dir, f"layer_{short_digest}.tar")
            with urllib.request.urlopen(blob_req, timeout=60) as blob_resp, open(temp_tar, "wb") as out_f:
                while True:
                    chunk = blob_resp.read(65536)
                    if not chunk:
                        break
                    out_f.write(chunk)

            # Unpack layer
            if progress_callback:
                progress_callback(f"Extracting layer {idx}/{len(layers)}: {short_digest}")

            try:
                with tarfile.open(temp_tar, "r:*") as tar:
                    tar.extractall(path=destination_dir)
            finally:
                if os.path.exists(temp_tar):
                    os.remove(temp_tar)

        return downloaded_digests
