from pathlib import Path

import numpy as np
import onnxruntime as ort

from app.services.preprocess import load_rgb_image, preprocess_for_keras_mobilenet, preprocess_for_onnx

THREE_CLASS_NAMES = ["Normal", "Early-stage Alzheimer's", "Advanced Alzheimer's"]

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = PROJECT_ROOT / "models"

ONNX_PATHS = [MODELS_DIR / "model.onnx"]
KERAS_PATHS = [
    MODELS_DIR / "model.h5",
    MODELS_DIR / "model.keras",
    MODELS_DIR / "Osteoporosis_Model_binary.h5",
]

# Notebook default labels often use these 4 classes.
NOTEBOOK_FOUR_CLASS = ["Mild Demented", "Moderate Demented", "Non Demented", "Very MildDemented"]


class Predictor:
    def __init__(self) -> None:
        self.backend: str | None = None
        self.session: ort.InferenceSession | None = None
        self.input_name: str | None = None
        self.input_shape: list | tuple | None = None
        self.keras_model = None
        self.class_names = THREE_CLASS_NAMES
        self.keras_four_class_names = NOTEBOOK_FOUR_CLASS
        self._load_model()

    def _load_model(self) -> None:
        onnx_path = next((path for path in ONNX_PATHS if path.exists()), None)
        if onnx_path is not None:
            self.session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
            self.input_name = self.session.get_inputs()[0].name
            self.input_shape = self.session.get_inputs()[0].shape
            self.keras_model = None
            self.backend = "onnx"
            self.class_names = THREE_CLASS_NAMES
            return

        keras_path = next((path for path in KERAS_PATHS if path.exists()), None)
        if keras_path is not None:
            try:
                from tensorflow.keras.models import load_model
            except Exception as exc:
                raise RuntimeError(
                    "Keras model detected but TensorFlow is not installed. "
                    "Install dependencies from requirements.txt and retry."
                ) from exc

            self.keras_model = load_model(str(keras_path), compile=False)
            self.session = None
            self.input_name = None
            self.input_shape = None
            self.backend = "keras"
            self.class_names = THREE_CLASS_NAMES
            return

        self.backend = None
        self.session = None
        self.input_name = None
        self.input_shape = None
        self.keras_model = None

    def _ensure_loaded(self) -> None:
        if self.backend is None:
            self._load_model()

        if self.backend is None:
            raise RuntimeError(
                "No model found. Place your model at models/model.onnx or models/model.h5 and retry."
            )

    @staticmethod
    def _softmax(logits: np.ndarray) -> np.ndarray:
        logits = logits - np.max(logits, axis=-1, keepdims=True)
        exp = np.exp(logits)
        return exp / np.sum(exp, axis=-1, keepdims=True)

    @staticmethod
    def _normalize_label(label: str) -> str:
        return "".join(ch.lower() for ch in label if ch.isalnum())

    def _aggregate_to_three_class(self, probs: np.ndarray, class_names: list[str]) -> dict[str, float]:
        if len(class_names) == 3:
            return {name: float(probs[idx]) for idx, name in enumerate(THREE_CLASS_NAMES)}

        if len(class_names) != 4:
            raise RuntimeError(
                f"Expected model to output 3 or 4 classes, but got {len(class_names)} classes."
            )

        normalized = {self._normalize_label(name): idx for idx, name in enumerate(class_names)}
        mild_idx = normalized.get("milddemented")
        very_mild_idx = normalized.get("verymilddemented")
        moderate_idx = normalized.get("moderatedemented")
        non_idx = normalized.get("nondemented")

        if None in (mild_idx, very_mild_idx, moderate_idx, non_idx):
            raise RuntimeError(
                "Unable to map 4-class output to clinical 3-class output. "
                "Expected labels compatible with Mild/VeryMild/Moderate/Non Demented."
            )

        early = float(probs[mild_idx] + probs[very_mild_idx])
        advanced = float(probs[moderate_idx])
        normal = float(probs[non_idx])

        return {
            "Normal": normal,
            "Early-stage Alzheimer's": early,
            "Advanced Alzheimer's": advanced,
        }

    def _resolve_class_names_for_vector(self, vector: np.ndarray) -> list[str]:
        count = int(vector.shape[0])
        if count == 3:
            return THREE_CLASS_NAMES
        if count == 4:
            return self.keras_four_class_names
        raise RuntimeError(f"Expected model to output 3 or 4 classes, but got {count} classes.")

    def _predict_vector_onnx(self, image_rgb: np.ndarray) -> np.ndarray:
        if self.session is None or self.input_name is None:
            raise RuntimeError("ONNX session is not initialized.")

        model_input = preprocess_for_onnx(image_rgb=image_rgb, input_shape=self.input_shape)
        outputs = self.session.run(None, {self.input_name: model_input})
        raw = np.array(outputs[0])

        if raw.ndim == 2:
            return raw[0].astype(np.float32)
        if raw.ndim == 1:
            return raw.astype(np.float32)

        raise RuntimeError("Unexpected ONNX model output shape.")

    def _predict_vector_keras(self, image_rgb: np.ndarray) -> np.ndarray:
        if self.keras_model is None:
            raise RuntimeError("Keras model is not initialized.")

        model_input = preprocess_for_keras_mobilenet(image_rgb)
        raw = np.array(self.keras_model.predict(model_input, verbose=0))

        if raw.ndim == 2:
            return raw[0].astype(np.float32)
        if raw.ndim == 1:
            return raw.astype(np.float32)

        raise RuntimeError("Unexpected Keras model output shape.")

    def predict(self, data: bytes) -> tuple[str, float, dict[str, float]]:
        self._ensure_loaded()
        image_rgb = load_rgb_image(data)

        if self.backend == "onnx":
            vector = self._predict_vector_onnx(image_rgb)
        elif self.backend == "keras":
            vector = self._predict_vector_keras(image_rgb)
        else:
            raise RuntimeError("No supported inference backend is active.")

        self.class_names = self._resolve_class_names_for_vector(vector)
        probs = self._softmax(vector.astype(np.float32))
        if probs.shape[0] != len(self.class_names):
            raise RuntimeError(
                f"Expected {len(self.class_names)} output classes, but got {probs.shape[0]}."
            )

        prob_map = self._aggregate_to_three_class(probs, self.class_names)
        top_label = max(prob_map, key=prob_map.get)
        top_conf = float(prob_map[top_label])

        return top_label, top_conf, prob_map
