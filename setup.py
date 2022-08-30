import setuptools
from setuptools import setup

with open("README.md", "r") as f:
    long_description = f.read()
    descr_lines = long_description.split("\n")
    long_description = "\n".join(descr_lines)


setup(
    # Information
    name="signal-slot-mp",
    description="Fast and compact framework for communication between threads and processes in Python using event loops, signals and slots.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    version="1.0.3",
    url="https://github.com/alex-petrenko/signal-slot",
    author="Aleksei Petrenko",
    license="MIT",
    keywords="asynchronous multithreading multiprocessing queue faster-fifo signal slot event loop",
    project_urls={
        "Github": "https://github.com/alex-petrenko/signal-slot",
        "Sample Factory": "https://github.com/alex-petrenko/sample-factory",
    },
    install_requires=[
        "faster-fifo>=1.4.2,<2.0",
    ],
    extras_require={
        "dev": ["black", "isort", "pytest<8.0", "flake8", "pre-commit", "twine"],
    },
    package_dir={"": "./"},
    packages=setuptools.find_packages(where="./", include="signal_slot*"),
    include_package_data=True,
    python_requires=">=3.8",
)
