import re
from pathlib import Path

from setuptools import find_packages, setup


with open("README.md", encoding="utf-8") as f:
    LONG_DESCRIPTION = f.read()


def read_version() -> str:
    """Read package version from spyder_image_viewer/__init__.py."""
    init_path = Path(__file__).parent / "spyder_image_viewer" / "__init__.py"
    content = init_path.read_text(encoding="utf-8")
    match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
    if not match:
        raise RuntimeError("Could not find __version__ in spyder_image_viewer/__init__.py")
    return match.group(1)


setup(
    name="spyder-image-viewer",
    version=read_version(),
    description="A lightweight NumPy array image viewer for Spyder",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    author="sk-ys",
    url="https://github.com/sk-ys/spyder_image_viewer",
    project_urls={
        "Bug Tracker": "https://github.com/sk-ys/spyder_image_viewer/issues",
        "Source Code": "https://github.com/sk-ys/spyder_image_viewer",
    },
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "spyder>=5.0",
        "numpy>=1.19",
        "qtpy>=2.0",
    ],
    entry_points={
        "spyder.plugins": [
            "image_viewer = spyder_image_viewer.plugin:ImageViewerPlugin",
        ]
    },
)
