
import json
import yaml
from fastapi.openapi.utils import get_openapi
from posture_estimation.main import app

def export_openapi():
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        description=app.description,
        routes=app.routes,
    )

    # Export as JSON
    with open("docs/openapi.json", "w") as f:
        json.dump(openapi_schema, f, indent=2)

    # Export as YAML
    with open("docs/openapi.yaml", "w") as f:
        yaml.dump(openapi_schema, f, sort_keys=False, allow_unicode=True)
        
    print("Exported openapi.json and openapi.yaml")

if __name__ == "__main__":
    export_openapi()
