import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pycolonies",
    version="1.0.16",
    author="Johan Kristiansson",
    author_email="johan.kristiansson@ri.se",
    description="Colonies Python SDK",
    long_description=long_description,
    py_modules=["pycolonies", "crypto", "cfs"],
    long_description_content_type="text/markdown",
    url="https://github.com/colonyos/pycolonies",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "requests>=2.27.1",
        "websocket-client>=1.3.1"
    ]
)
