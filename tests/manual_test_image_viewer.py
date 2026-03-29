"""Generate sample NumPy arrays for Spyder Image Viewer manual testing."""

import numpy as np


def create_test_arrays():
    """Return representative image arrays for manual plugin testing."""
    arrays = {}

    # Grayscale gradient
    arrays["grayscale"] = (
        np.linspace(0, 255, 256, dtype=np.uint8)
        .repeat(256)
        .reshape(256, 256)
    )

    # RGB random image
    arrays["rgb_random"] = np.random.randint(
        0, 256, (240, 320, 3), dtype=np.uint8
    )

    # RGBA image with alpha gradient
    rgba = np.random.randint(0, 256, (180, 320, 4), dtype=np.uint8)
    rgba[..., 3] = np.linspace(0, 255, 320, dtype=np.uint8)
    arrays["rgba_alpha"] = rgba

    # Float range [0, 1]
    x = np.linspace(0, 4 * np.pi, 256)
    y = np.linspace(0, 4 * np.pi, 256)
    xx, yy = np.meshgrid(x, y)
    arrays["float_wave"] = (np.sin(xx) * np.cos(yy) + 1.0) / 2.0

    return arrays


if __name__ == "__main__":
    print("=" * 60)
    print("Creating test image arrays...")
    print("=" * 60)

    test_arrays = create_test_arrays()
    for name, arr in test_arrays.items():
        print(f"{name:>12} | shape={arr.shape} dtype={arr.dtype}")

    globals().update(test_arrays)

    print("\nArrays injected into globals().")
    print("Open Spyder Variable Explorer and select each array.")
