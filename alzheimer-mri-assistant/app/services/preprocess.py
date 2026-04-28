from io import BytesIO

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError

TARGET_SIZE = (224, 224)


def load_rgb_image(data: bytes, target_size: tuple[int, int] = TARGET_SIZE) -> np.ndarray:
    """Load image bytes to RGB array resized to target size."""
    try:
        image = Image.open(BytesIO(data)).convert("RGB")
    except UnidentifiedImageError as exc:
        raise ValueError("Unsupported or corrupted image file.") from exc

    arr = np.array(image)
    arr = cv2.GaussianBlur(arr, (3, 3), 0)
    arr = cv2.resize(arr, target_size, interpolation=cv2.INTER_AREA)

    return arr.astype(np.float32)


def preprocess_for_onnx(image_rgb: np.ndarray, input_shape: list | tuple | None = None) -> np.ndarray:
    """Prepare tensor for ONNX models that may expect NCHW or NHWC and 1 or 3 channels."""
    if input_shape and len(input_shape) == 4:
        channel_dim = input_shape[1]
        if channel_dim == 3:
            arr = image_rgb / 255.0
            arr = np.transpose(arr, (2, 0, 1))  # HWC -> CHW
            return np.expand_dims(arr, axis=0).astype(np.float32)

        if channel_dim == 1:
            gray = cv2.cvtColor(image_rgb.astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32)
            gray = gray / 255.0
            gray = np.expand_dims(gray, axis=0)
            return np.expand_dims(gray, axis=0).astype(np.float32)

        if input_shape[-1] == 3:
            arr = image_rgb / 255.0
            return np.expand_dims(arr, axis=0).astype(np.float32)

    # Safe default for common ONNX exports from PyTorch: NCHW RGB.
    arr = image_rgb / 255.0
    arr = np.transpose(arr, (2, 0, 1))
    return np.expand_dims(arr, axis=0).astype(np.float32)


def preprocess_for_keras_mobilenet(image_rgb: np.ndarray) -> np.ndarray:
    """Prepare tensor for Keras models trained with MobileNetV2 preprocessing."""
    from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

    batch = np.expand_dims(image_rgb, axis=0).astype(np.float32)
    return preprocess_input(batch)
