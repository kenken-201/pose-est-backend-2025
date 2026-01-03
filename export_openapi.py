"""FastAPI OpenAPI スキーマをエクスポートするスクリプト。

Usage:
    poetry run python export_openapi.py
"""
import json
import logging
from pathlib import Path

import yaml
from fastapi.openapi.utils import get_openapi

from posture_estimation.main import app

logger = logging.getLogger(__name__)


def export_openapi() -> None:
    """OpenAPI スキーマを JSON と YAML 形式でエクスポートします。"""
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        description=app.description,
        routes=app.routes,
    )

    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)

    # Export as JSON
    with (docs_dir / "openapi.json").open("w") as f:
        json.dump(openapi_schema, f, indent=2)

    # Export as YAML
    with (docs_dir / "openapi.yaml").open("w") as f:
        yaml.dump(openapi_schema, f, sort_keys=False, allow_unicode=True)

    logger.info("Exported openapi.json and openapi.yaml to %s", docs_dir)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    export_openapi()
