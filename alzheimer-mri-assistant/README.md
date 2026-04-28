# MRI Alzheimer Decision Support

A lightweight web app + API that accepts an MRI image and classifies it into:

- Normal
- Early-stage Alzheimer's
- Advanced Alzheimer's

> This system is for clinical decision support only and is not a standalone diagnosis.

## 1) Project structure

```
alzheimer-mri-assistant/
  app/
    main.py
    schemas.py
    services/
      preprocess.py
      inference.py
      explain.py
    static/
      index.html
      styles.css
      app.js
  models/
    model.onnx   # supported
    model.h5     # supported (from notebook)
  requirements.txt
  README.md
```

## 2) Add your ready model

Place your model in one of these paths:

- `models/model.onnx`
- `models/model.h5`

These files are intentionally not meant to be committed to GitHub. The sample model in this workspace is larger than the normal GitHub file limit, so keep trained weights local or store them with Git LFS or as a separate release asset.

### Expected model contract

- Input image size: `224x224`
- Output: logits/probabilities for either 3 classes or 4 classes.

For 3-class output, expected order:
  1. Normal
  2. Early-stage Alzheimer's
  3. Advanced Alzheimer's

For 4-class notebook output, expected labels compatible with:
- Mild Demented
- Very MildDemented
- Moderate Demented
- Non Demented

The API automatically maps them to clinical 3-class output:
- Normal = Non Demented
- Early-stage Alzheimer's = Mild + Very Mild
- Advanced Alzheimer's = Moderate

## 3) Run locally

```bash
cd alzheimer-mri-assistant
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

If you are already inside the project folder, you can skip the `cd` line.

Open:

- UI: `http://127.0.0.1:8000/`
- Health: `http://127.0.0.1:8000/api/health`

### One-click Windows startup

You can run everything with one file:

```bat
run_project.bat
```

It will create `.venv` (if missing), install dependencies, open the browser, and start the app on port `8010`.

## 4) API usage

### POST `/api/predict`

Form-data field:

- `file`: image file

Response example:

```json
{
  "label": "Early-stage Alzheimer's",
  "confidence": 0.82,
  "probabilities": {
    "Normal": 0.11,
    "Early-stage Alzheimer's": 0.82,
    "Advanced Alzheimer's": 0.07
  },
  "explanation": "The scan pattern is more consistent with early-stage Alzheimer's...",
  "disclaimer": "This output is a decision-support aid only and is not a standalone diagnosis. Final medical judgment must be made by a qualified physician."
}
```

## 5) Notes

- Model loading priority is: `model.onnx` then `model.h5`.
- If no model exists in `models/`, the API returns HTTP 503 with guidance.
- For H5 models trained with MobileNetV2 preprocessing, normalization is applied automatically.
- Large local artifacts such as `archive/`, `.venv/`, `brain.venv/`, and model binaries are ignored by default so the repo stays GitHub-friendly.
