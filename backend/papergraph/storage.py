import hashlib
import os
import re
import tempfile
from pathlib import Path


class DocumentStorage:
    def __init__(self, directory: Path):
        self.directory = directory.resolve()
        self.directory.mkdir(parents=True, exist_ok=True)

    def path(self, digest: str) -> Path:
        if not re.fullmatch(r"[a-f0-9]{64}", digest):
            raise ValueError("Invalid source hash")
        return self.directory / f"{digest}.pdf"

    def put(self, content: bytes) -> str:
        digest = hashlib.sha256(content).hexdigest()
        target = self.path(digest)
        if target.is_symlink():
            raise ValueError("Unsafe storage target")
        if target.exists():
            self.read(digest)
            return digest
        handle, name = tempfile.mkstemp(dir=self.directory, suffix=".tmp")
        try:
            with os.fdopen(handle, "wb") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(name, target)
        finally:
            if os.path.exists(name):
                os.unlink(name)
        return digest

    def read(self, digest: str) -> bytes:
        path = self.path(digest)
        if path.is_symlink():
            raise ValueError("Unsafe storage target")
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != digest:
            raise ValueError("Source hash mismatch")
        return content
