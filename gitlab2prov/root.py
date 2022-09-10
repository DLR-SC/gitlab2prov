from pathlib import Path


def get_package_root() -> Path:
    return Path(__file__).parent