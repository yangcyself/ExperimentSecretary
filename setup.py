import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="experimentSecretary", 
    version="0.1.1",
    author="yangcyself",
    author_email="yangcyself@sjtu.edu.cn",
    description="A package for utilities for experiments",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yangcyself/ExperimentSecretary",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
)