"""Shared test fixtures and utilities for toolbox tests."""

from pathlib import Path

import pytest


@pytest.fixture
def test_assets_dir():
    """Path to the test assets directory"""
    return Path(__file__).parent / "assets"
