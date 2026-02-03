from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="purpleair-calibration",
    version="1.0.0",
    author="Yunqian Zhang, Yan Rong, Lu Liang",
    author_email="lianglu@berkeley.edu",
    description="Machine learning calibration framework for PurpleAir temperature sensors",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/purpleair-calibration",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/purpleair-calibration/issues",
        "Documentation": "https://github.com/yourusername/purpleair-calibration/docs",
        "Source Code": "https://github.com/yourusername/purpleair-calibration",
        "Web Interface": "https://huggingface.co/spaces/yunqianz/purpleair-calibration",
    },
    packages=find_packages(exclude=["tests", "tests.*", "docs", "notebooks"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Atmospheric Science",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.2.0",
            "pytest-cov>=3.0.0",
            "black>=21.0",
            "flake8>=3.9.0",
            "mypy>=0.910",
            "pre-commit>=2.15.0",
            "isort>=5.9.0",
        ],
        "docs": [
            "sphinx>=4.0.0",
            "sphinx-rtd-theme>=1.0.0",
            "nbsphinx>=0.8.0",
        ],
        "gpu": [
            "cupy-cuda11x>=10.0.0",  # Replace with appropriate CUDA version
        ],
    },
    entry_points={
        "console_scripts": [
            "purpleair-calibrate=scripts.run_calibration:main",
            "purpleair-download=data.download_purpleair:main",
            "purpleair-train=models.train_xgboost:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json"],
    },
    keywords=[
        "purpleair",
        "temperature",
        "calibration",
        "machine learning",
        "xgboost",
        "environmental monitoring",
        "heat exposure",
        "urban climate",
        "low-cost sensors",
    ],
)
