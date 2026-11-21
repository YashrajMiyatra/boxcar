<div align="center">

# 📦 Boxcar

### Lightweight Linux Container Runtime & Docker Hub Image Puller from Scratch

[![CI](https://github.com/YashrajMiyatra/boxcar/actions/workflows/ci.yml/badge.svg)](https://github.com/YashrajMiyatra/boxcar/actions)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Dependencies](https://img.shields.io/badge/dependencies-zero-success.svg)](https://github.com)

*A minimalist container engine inspired by runc, Docker, and Linux kernel isolation primitives.*

</div>

---

## 💡 What is Boxcar?

Ever wondered what `docker run` actually does under the hood?

**Boxcar** is a container runtime built with **zero external dependencies** that implements:
1. **OCI & Docker Registry v2 Client**: Speaks the native Docker Hub protocol, exchanges bearer tokens, fetches manifests, and streams real compressed image layer blobs (`.tar.gz`).
2. **Layered RootFS Extraction**: Unpacks and merges OCI image layers into isolated local container filesystems.
3. **Resource Guard (Cgroups/rlimit)**: Enforces hard memory boundaries (`-m 50MB`) and CPU quotas on container processes.
4. **Process Sandboxing**: Isolates process groups (`setsid`), environments, and working directories.
5. **CLI Interface**: Native commands like `boxcar pull`, `boxcar images`, and `boxcar run`.

---

## 🚀 Quickstart

### 1. Pull a Real Image from Docker Hub
Download and extract Alpine Linux directly from Docker Hub:

```bash
python3 -m boxcar.cli pull alpine
```

### 2. List Local Images
```bash
python3 -m boxcar.cli images
```

Output:
```text
REPOSITORY                TAG          IMAGE ID        SIZE        
-----------------------------------------------------------------
alpine                    latest       43c626077c68    7.8 MB      
```

### 3. Run Commands in Isolation
Run a container with a 64 MB memory limit:

```bash
python3 -m boxcar.cli run -m 64 alpine /bin/echo "Hello from Boxcar container!"
```

Pass custom environment variables with `-e / --env`:
```bash
python3 -m boxcar.cli run -e APP_ENV=production -m 64 alpine /bin/sh -c "echo \$APP_ENV"
```

---

## 🧪 Testing

Run the automated test suite:
```bash
python3 -m unittest discover -s tests -v
```

---

## 📜 License

MIT License. See [LICENSE](LICENSE) for details.
