import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pySteer-Jonas-Kunath",
    version="0.1",
    author="Jonas Kunath",
    author_email="kunath@llr.in2p3.fr",
    description="Wrapper for the iLCSoft Marlin steering file production.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="github.com/kunathj/pySteer",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
