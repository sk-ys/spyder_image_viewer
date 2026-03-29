from setuptools import find_packages, setup


with open("README.md", encoding="utf-8") as f:
    LONG_DESCRIPTION = f.read()


setup(
    name="spyder-image-viewer",
    version="0.1.0",
    description="A lightweight NumPy array image viewer for Spyder",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    author="sk-ys",
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
