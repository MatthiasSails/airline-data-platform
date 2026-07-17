"""Pydantic request/response models for the flight delay prediction API."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FlightFeatures(BaseModel):
    Time: float = Field(
        ..., ge=0, le=1439, description="Scheduled departure, minutes since midnight"
    )
    Length: float = Field(..., gt=0, description="Flight duration in minutes")
    Airline: str = Field(..., min_length=1, max_length=10, description="IATA carrier code")
    AirportFrom: str = Field(..., min_length=3, max_length=4, description="Origin IATA airport code")
    AirportTo: str = Field(..., min_length=3, max_length=4, description="Destination IATA airport code")
    DayOfWeek: int = Field(..., ge=1, le=7, description="1=Monday .. 7=Sunday")

    @field_validator("Airline", "AirportFrom", "AirportTo")
    @classmethod
    def uppercase_codes(cls, v: str) -> str:
        return v.strip().upper()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "Time": 1296,
                "Length": 141,
                "Airline": "DL",
                "AirportFrom": "ATL",
                "AirportTo": "HOU",
                "DayOfWeek": 1,
            }
        }
    )


class PredictionResponse(BaseModel):
    predicted_class: int
    predicted_label: str
    probability_delayed: float


class BatchPredictionRequest(BaseModel):
    records: list[FlightFeatures]


class BatchPredictionResponse(BaseModel):
    predictions: list[PredictionResponse]


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool


class ModelInfoResponse(BaseModel):
    model_name: str
    model_version: str
    trained_at_utc: str
    test_metrics: dict
    raw_feature_schema: dict
    class_labels: dict
