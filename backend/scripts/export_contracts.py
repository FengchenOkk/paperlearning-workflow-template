"""Export Pydantic contracts as JSON Schema; frontend types are generated from this file."""

import argparse
import json
from pathlib import Path

from pydantic import BaseModel
from pydantic.json_schema import models_json_schema

from papergraph import schemas


def main() -> None:
    models = [
        value
        for value in vars(schemas).values()
        if isinstance(value, type)
        and issubclass(value, BaseModel)
        and value not in {BaseModel, schemas.Contract}
    ]
    _, schema = models_json_schema(
        [(model, "validation") for model in models], title="PaperGraph contracts"
    )
    output = Path(__file__).resolve().parents[2] / "packages" / "schemas" / "domain.schema.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(schema, indent=2) + "\n"
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    if parser.parse_args().check:
        if output.read_text(encoding="utf-8") != content:
            raise ValueError("Generated JSON Schema is stale")
    else:
        output.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
