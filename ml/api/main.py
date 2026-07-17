"""FastAPI service for predicting airline flight delay status.

Run locally with:
    uvicorn api.main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from .dependencies import model_service
from .schemas import (
    BatchPredictionRequest,
    BatchPredictionResponse,
    FlightFeatures,
    HealthResponse,
    ModelInfoResponse,
    PredictionResponse,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    model_service.load()
    yield


app = FastAPI(
    title="Airline Flight Delay Prediction API",
    description="Predicts whether a flight will be delayed (Class=1) or on-time (Class=0).",
    version="1.0.0",
    lifespan=lifespan,
)


def _require_model_loaded():
    if not model_service.is_loaded:
        raise HTTPException(status_code=503, detail="Model is not loaded.")


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok", model_loaded=model_service.is_loaded)


@app.get("/model/info", response_model=ModelInfoResponse)
def model_info():
    _require_model_loaded()
    meta = model_service.metadata
    return ModelInfoResponse(
        model_name=meta["model_name"],
        model_version=meta["model_version"],
        trained_at_utc=meta["trained_at_utc"],
        test_metrics=meta["test_metrics"],
        raw_feature_schema=meta["raw_feature_schema"],
        class_labels=meta["class_labels"],
    )


@app.post("/predict", response_model=PredictionResponse)
def predict_single(flight: FlightFeatures):
    _require_model_loaded()
    result = model_service.predict([flight.model_dump()])[0]
    return PredictionResponse(**result)


@app.post("/predict/batch", response_model=BatchPredictionResponse)
def predict_batch(batch: BatchPredictionRequest):
    _require_model_loaded()
    records = [record.model_dump() for record in batch.records]
    results = model_service.predict(records)
    return BatchPredictionResponse(
        predictions=[PredictionResponse(**r) for r in results]
    )
