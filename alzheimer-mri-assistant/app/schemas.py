from pydantic import BaseModel, Field


class PredictResponse(BaseModel):
    label: str = Field(description="Top predicted class label")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score for top prediction")
    probabilities: dict[str, float] = Field(description="Probability per class")
    explanation: str = Field(description="Simple human-readable explanation")
    disclaimer: str = Field(description="Medical safety disclaimer")
