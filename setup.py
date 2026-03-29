from setuptools import find_packages, setup


with open("README.md", encoding="utf-8") as f:
    LONG_DESCRIPTION = f.read()


setup(
    name="spyder-image-viewer",
    version="0.1.2",
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
