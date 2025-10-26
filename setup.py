"""
PyCalendar - Sports Scheduling System
Setup configuration file
"""

from setuptools import setup, find_packages
from pathlib import Path

# Lire le README pour la description longue
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="pycalendar",
    version="2.0.0",
    author="VinCheetah",
    description="Système de planification automatique de calendriers sportifs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/VinCheetah/PyCalendar",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.8",
    install_requires=[
        "pandas>=2.0.0",
        "openpyxl>=3.1.0",
        "pyyaml>=6.0",
        "ortools>=9.7.0",
        "streamlit>=1.28.0",
        "plotly>=5.17.0",
        "jsonschema>=4.19.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
            "isort>=5.12.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "pycalendar=pycalendar.__main__:main",
            "pycalendar-config=pycalendar.cli.config_tools:main",
            "pycalendar-extract=pycalendar.cli.pool_extractor:main",
            "pycalendar-sheet=pycalendar.cli.match_sheet_generator:main",
            "pycalendar-import=pycalendar.cli.external_importer:main",
            "pycalendar-validate=pycalendar.cli.solution_validator:main",
            "pycalendar-check=pycalendar.cli.quality_checker:main",
            "pycalendar-interface=pycalendar.cli.interface_regenerator:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,
    package_data={
        "pycalendar": [
            "interface/templates/*.html",
            "interface/assets/**/*",
            "interface/scripts/**/*.js",
            "interface/data/schemas/*.json",
        ],
    },
)
