#!/usr/bin/env python3
"""
Setup script for Clinical Trials MCP Server
"""

from setuptools import setup, find_packages
import os

# Read README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="clintrials-mcp",
    version="1.0.0",
    author="Clinical Trials MCP Team",
    author_email="your-email@example.com",
    description="MCP server for accessing and analyzing clinical trials data from ClinicalTrials.gov",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/clintrials-mcp",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Healthcare Industry",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.910",
        ],
    },
    entry_points={
        "console_scripts": [
            "clintrials-mcp=mcp_server:cli_main",
        ],
    },
    scripts=[
        "bin/clintrials-mcp",
    ],
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.dxt", "*.json"],
    },
    project_urls={
        "Bug Reports": "https://github.com/yourusername/clintrials-mcp/issues",
        "Source": "https://github.com/yourusername/clintrials-mcp",
        "Documentation": "https://github.com/yourusername/clintrials-mcp#readme",
    },
)