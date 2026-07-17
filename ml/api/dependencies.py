"""Model loading singleton for the FastAPI app."""

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
