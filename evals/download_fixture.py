"""Explicit public fixture download. Never scans local research directories."""
import hashlib
import json
import argparse
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent
args = argparse.ArgumentParser()
args.add_argument("fixture", choices=["dropout", "gw150914"], default="dropout", nargs="?")
fixture = args.parse_args().fixture
manifest = json.loads((ROOT / f"{fixture}.json").read_text(encoding="utf-8"))
target = ROOT / "private" / f"{fixture}.pdf"
target.parent.mkdir(parents=True, exist_ok=True)
if not target.exists():
    with urlopen(manifest["pdf_url"], timeout=30) as response:
        content = response.read(10 * 1024 * 1024)
    if not content.startswith(b"%PDF-"):
        raise ValueError("Fixture URL did not return a PDF")
    target.write_bytes(content)
actual_hash = hashlib.sha256(target.read_bytes()).hexdigest()
if actual_hash != manifest["sha256"]:
    raise ValueError("Public fixture changed; review the source and update the golden manifest explicitly")
print("Fixture SHA-256:", actual_hash)
