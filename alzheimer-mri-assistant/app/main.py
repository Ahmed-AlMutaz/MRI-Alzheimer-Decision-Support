from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.schemas import PredictResponse
from app.services.explain import build_explanation
from app.services.inference import Predictor

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="MRI Alzheimer Decision Support API",
    version="0.1.0",
    description="Decision-support API for classifying MRI scans into normal, early-stage, or advanced Alzheimer's.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

predictor = Predictor()


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/predict", response_model=PredictResponse)
async def predict(file: UploadFile = File(...)) -> PredictResponse:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are supported.")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        label, confidence, probabilities = predictor.predict(data)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    explanation = build_explanation(label=label, confidence=confidence)

    return PredictResponse(
        label=label,
        confidence=confidence,
        probabilities=probabilities,
        explanation=explanation,
        disclaimer=(
            "This output is a decision-support aid only and is not a standalone diagnosis."
            " Final medical judgment must be made by a qualified physician."
        ),
    )
