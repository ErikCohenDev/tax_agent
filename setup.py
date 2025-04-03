"""
Setup script for Tax Agent package.
"""

from setuptools import setup, find_packages

setup(
    name="tax_agent",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "lxml",
        "beautifulsoup4",
        "bs4",
        "ollama",
    ],
    extras_require={
        "dev": [
            "flake8",
            "black",
            "isort",
            "mypy",
            "pytest",
            "pytest-cov",
        ],
    },
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "tax-agent=src.main:main",
        ],
    },
)
