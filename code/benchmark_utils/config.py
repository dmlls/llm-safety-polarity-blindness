"""Configuration for the benchmark utilities."""

from pathlib import Path

# BENCHMARK_DIR: Path = Path("../../dataset_full")
BENCHMARK_DIR: Path = Path(".")

LANGUAGES: list[str] = ["en", "es", "cs"]

VALIDATE: list[str] = ["synonyms"]
