from fastapi import FastAPI

app = FastAPI(
    title="Pose Estimation Backend",
    description="Backend API for Pose Estimation using TensorFlow MoveNet",
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint to verify service status.

    Returns:
        dict[str, str]: Status of the service.
    """
    return {"status": "ok"}
