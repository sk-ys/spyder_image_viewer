"""Validation and conversion helpers for image-like NumPy arrays."""

from __future__ import annotations

import numpy as np


def is_image_array(obj: object) -> bool:
    """Return True when *obj* is a supported image ndarray."""
    if not isinstance(obj, np.ndarray):
        return False

    if obj.ndim == 2:
        return True

    if obj.ndim == 3 and obj.shape[2] >= 1:
        return True

    return False


def normalize_image_array(array: np.ndarray) -> np.ndarray:
    """Normalize supported arrays to uint8 for display."""
    arr = np.asarray(array)

    if arr.dtype == np.uint8:
        return arr

    if np.issubdtype(arr.dtype, np.floating):
        arr_min = float(np.nanmin(arr))
        arr_max = float(np.nanmax(arr))

        if arr_min >= 0.0 and arr_max <= 1.0:
            scaled = arr * 255.0
        elif arr_min >= 0.0 and arr_max <= 255.0:
            scaled = arr
        else:
            denom = arr_max - arr_min
            if denom == 0:
                scaled = np.zeros_like(arr)
            else:
                scaled = (arr - arr_min) / denom * 255.0

        return np.clip(scaled, 0.0, 255.0).astype(np.uint8)

    return np.clip(arr, 0, 255).astype(np.uint8)
