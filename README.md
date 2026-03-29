# Spyder Image Viewer Plugin

A lightweight image viewer plugin for Spyder focused on fast NumPy array inspection.

<table><tr>
<td><img src="docs\images\sample1.png"></td>
<td><img src="docs\images\sample2.png"></td>
</tr></table>

## Notice

This plugin was generated almost entirely (nearly 100%) with GitHub Copilot.

## Highlights

- Fast rendering at high zoom levels using viewport-only drawing.
- Docked viewer integrated with Spyder Variable Explorer.
- Optional popup viewers from Variable Explorer context menu.
- Nearest-neighbor scaling (no blur) for pixel-accurate inspection.
- Zoom range from 10% to 3000%.
- Pixel grid and value overlay at 3000% (`Show Pixels`).
- Hover tooltip with coordinate and value/intensity.
- Channel selector for 3D images (`full`, or per-channel grayscale view).

## Supported Input

The plugin accepts NumPy arrays with:

- `H x W` (2D)
- `H x W x C` (3D, `C >= 1`)

There is no fixed channel-count restriction in 3D mode. For example, `H x W x 10` is supported.

Accepted dtypes include integer and floating-point arrays. Arrays are normalized to `uint8` for display.

Float normalization behavior:

- `[0, 1]` -> scaled to `[0, 255]`
- `[0, 255]` -> used as-is
- other ranges -> min-max normalized to `[0, 255]`

## Requirements

- Python >= 3.7
- Spyder >= 5.0
- NumPy >= 1.19
- QtPy >= 2.0

## Installation

### Option 1: Editable install (recommended for local development)

```bash
cd spyder_image_viewer
pip install -e .
```

This allows you to edit the source code and see changes reflected immediately.

### Option 2: Standard install

```bash
cd spyder_image_viewer
pip install .
```

### Verify installation

After installation, restart Spyder and check:

```
Tools → Preferences → Plugins
```

Confirm `Image Viewer` is listed and enabled.

## Usage

1. Start Spyder.
2. Create an image-like NumPy array:

```python
import numpy as np

img = np.random.randint(0, 256, (1080, 1920, 3), dtype=np.uint8)
```

3. In Variable Explorer, select `img`.
4. The image appears in the `Image Viewer` dock.

You can also right-click a variable and choose `Open in Image Viewer` to open an independent popup window.

## Controls

- Zoom slider: `10%` to `3000%`
- Mouse wheel: normal scrolling
- `Ctrl + wheel`: nonlinear zoom
- Zoom anchor: cursor-centered when over image, otherwise viewport-centered
- `Show Pixels`: jump to `3000%` temporarily and restore previous zoom when toggled off
- `Channel` combo (3D images):
  - `full` shows color image
  - numeric channels show single-channel grayscale

## Pixel Overlay and Tooltip

At `3000%`, the viewer can render:

- pixel grid
- per-pixel values (in single-channel mode)

Hover tooltip:

- `Coord: (x, y)`
- `Intensity: ...` for scalar views
- `Value: (...)` for multi-channel views

## Project Structure

```text
spyder_image_viewer/
├── setup.py
├── setup.cfg
├── README.md
├── README.ja.md
├── docs/
│   ├── quickstart.md
│   ├── development_guide.md
│   └── ja/
│       ├── quickstart.ja.md
│       └── development_guide.ja.md
├── spyder_image_viewer/
│   ├── plugin.py
│   ├── widgets/
│   │   └── image_viewer.py
│   └── utils/
│       └── array_validator.py
└── tests/
    └── manual_test_image_viewer.py
```

## Development

Run the test script:

```bash
python tests/manual_test_image_viewer.py
```

Or in a Spyder console:

```python
exec(open('tests/manual_test_image_viewer.py').read())
```

## Troubleshooting

### Plugin not found

1. Reinstall in editable mode:

```bash
pip uninstall spyder-image-viewer
pip install -e .
```

2. Restart Spyder completely.

3. If needed, clear Spyder cache:

```bash
rm -rf ~/.spyder-py3/
```

### Dock is hidden

Open in Spyder:

```
View → Docks → Image Viewer
```

### "Not a valid image array"

Verify array shape:

```python
from spyder_image_viewer.utils import is_image_array
print(is_image_array(your_array))
```

Supported shapes:

- 2D: `(H, W)`
- 3D: `(H, W, C)` where `C >= 1`


## License

MIT License


