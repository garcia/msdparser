from setuptools import setup

from msdparser import __version__ as version


with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="msdparser",
    version=version,
    description="Robust & lightning fast MSD parser (StepMania file format)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Ash Garcia",
    author_email="python-msdparser@garcia.sh",
    url="http://github.com/garcia/msdparser",
    packages=["msdparser"],
    package_data={
        "msdparser": ["py.typed"],
    },
    include_package_data=True,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3",
        "Topic :: Games/Entertainment",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Typing :: Typed",
    ],
    license="MIT",
    keywords="stepmania simfile sm ssc dwi",
    python_requires=">=3.6",
    zip_safe=False,
    command_options={
        "build_sphinx": {
            "version": ("setup.py", version),
        },
    },
)
