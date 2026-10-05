import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    database_url: str = "sqlite:///./data/papergraph.db"
    storage_dir: Path = Path("data/documents")
    max_upload_bytes: int = 25 * 1024 * 1024
    max_pages: int = 300
    lease_seconds: int = 300

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            database_url=os.environ.get("PAPERGRAPH_DATABASE_URL", cls.database_url),
            storage_dir=Path(os.environ.get("PAPERGRAPH_STORAGE_DIR", "data/documents")),
        )
