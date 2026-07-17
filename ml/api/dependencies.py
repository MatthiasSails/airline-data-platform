"""Model loading singleton for the FastAPI app."""

import os

from fastapi import Header, HTTPException

from src.airline_delay import predict


class ModelService:
    def __init__(self):
        self.pipeline = None
        self.metadata = None

    def load(self):
        self.pipeline = predict.load_model()
        self.metadata = predict.load_metadata()

    @property
    def is_loaded(self) -> bool:
        return self.pipeline is not None

    def predict(self, records: list[dict]) -> list[dict]:
        return predict.predict(self.pipeline, records)


model_service = ModelService()


def require_api_key(x_api_key: str = Header(default=None)):
    expected = os.environ.get("ML_API_KEY")
    if not expected:
        raise HTTPException(status_code=503, detail="API key is not configured.")
    if x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")
