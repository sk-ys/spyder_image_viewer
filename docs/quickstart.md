# Spyder Image Viewer Plugin - Quick Start

Get running in about 5 minutes.

## 1. Install

```bash
cd spyder_image_viewer
pip install .
```

## 2. Restart Spyder

```bash
spyder
```

## 3. Create test arrays

Run in Spyder console:

```python
import numpy as np

img = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
img10 = np.random.randint(0, 256, (100, 100, 10), dtype=np.uint8)
```

## 4. Open in Image Viewer

1. Click the variable in Variable Explorer.
2. Check the `Image Viewer` dock.
3. Try zoom and channel switching.

## Useful checks

- Zoom to `3000%`
- Enable `Show Pixels`
- Hover to see `Coord` + `Intensity/Value`
- For 3D arrays, switch between `full` and channel indices
- In `full` mode with 3+ channels, test `Order: RGB/BGR`

## Common issues

### `No module named spyder_image_viewer`

```bash
pip install .
```

This error usually means the plugin is not installed in the Python environment used by Spyder.

### Plugin is not visible

Open:

`View -> Docks -> Image Viewer`

### Array is rejected

Use supported shapes:

- `(H, W)`
- `(H, W, C)` where `C >= 1`

## Next docs

- `docs/development_guide.md`
- `docs/ja/quickstart.ja.md`


