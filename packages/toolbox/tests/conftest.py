"""Shared test fixtures and utilities for toolbox tests."""

from pathlib import Path

import pytest


@pytest.fixture
def test_assets_dir():
    """Path to the test assets directory"""
    return Path(__file__).parent / "assets"


@pytest.fixture
def test_script_path(test_assets_dir):
    """Path to the test script for integration tests"""
    script_path = test_assets_dir / "test_event_script.py"
    assert script_path.exists(), f"Test script not found: {script_path}"
    return script_path
