# Spyder Image Viewer Plugin - Implementation Guide

This document explains the current plugin architecture and extension points.

## Current structure

```text
spyder_image_viewer/
├── setup.py
├── setup.cfg
├── docs/
│   ├── quickstart.md
│   ├── development_guide.md
│   └── ja/
│       ├── quickstart.ja.md
│       └── development_guide.ja.md
└── spyder_image_viewer/
    ├── plugin.py
    ├── widgets/
    │   └── image_viewer.py
    └── utils/
        └── array_validator.py
```

## Core components

## `plugin.py`

- Defines `ImageViewerPlugin` (`SpyderDockablePlugin`)
- Integrates with Variable Explorer
- Adds `Open in Image Viewer` context action
- Supports independent popup windows

## `widgets/image_viewer.py`

- Main UI and rendering logic
- Fast viewport-only painter (`_FastImageLabel`)
- Zoom model (`10%` to `3000%`)
- Ctrl+wheel nonlinear zoom
- Pixel grid/value overlay for high zoom mode
- Hover tooltip with coordinate and value(s)

## `utils/array_validator.py`

- `is_image_array`: accepts `(H, W)` and `(H, W, C)` with `C >= 1`
- `normalize_image_array`: converts display data to `uint8`

## Rendering behavior

- Nearest-neighbor display (`SmoothPixmapTransform = False`)
- Scroll + zoom anchor preservation
- Overlay drawn only in visible viewport

## Channel behavior

- 2D: grayscale mode
- 3D: `full` + per-channel selection
- For arrays with 3+ channels, `full` renders the first 3 channels as the color image
- `Order` selector supports `RGB` / `BGR` switching in full mode
- Full mode tooltip can display all channel values

## Packaging

`setup.py` registers the plugin via:

```python
entry_points={
    "spyder.plugins": [
        "image_viewer = spyder_image_viewer.plugin:ImageViewerPlugin",
    ]
}
```

## Suggested development workflow

1. Edit code
2. `pip install -e .` (if needed)
3. Restart Spyder
4. Test with 2D and 3D arrays (including multi-channel 3D, e.g. `C=10`)

## Related docs

- `docs/quickstart.md`
- `docs/ja/development_guide.ja.md`


