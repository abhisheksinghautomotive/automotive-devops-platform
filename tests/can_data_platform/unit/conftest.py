"""Shared pytest fixtures and configuration.

This module provides common fixtures and utilities for all test modules.
"""

import json
import os
import tempfile

import pytest


@pytest.fixture
def sample_battery_event():
    """Provide a sample battery cell event for testing.

    Returns:
        dict: A sample battery event with typical cell voltages.
    """
    return {
        "Cell1Voltage": 3800,
        "Cell2Voltage": 3850,
        "Cell3Voltage": 3900,
        "Cell4Voltage": 3950,
        "min_voltage": 3800,
        "max_voltage": 3950,
        "avg_voltage": 3875,
        "module_offsets": [-10, 5, 20, 15],
    }


@pytest.fixture
def sample_events_list():
    """Provide a list of sample battery events for testing.

    Returns:
        list: A list of sample battery events.
    """
    return [
        {"Cell1Voltage": 3800, "Cell2Voltage": 3850},
        {"Cell1Voltage": 3900, "Cell2Voltage": 3950},
        {"Cell1Voltage": 4000, "Cell2Voltage": 4050},
    ]


@pytest.fixture
def temp_jsonl_file(
    sample_events_list,
):  # pylint: disable=redefined-outer-name
    """Create a temporary JSONL file with sample events.

    Args:
        sample_events_list: Fixture providing sample events.

    Yields:
        str: Path to the temporary JSONL file.
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".jsonl", delete=False
    ) as tmp_file:
        for event in sample_events_list:
            tmp_file.write(json.dumps(event) + "\n")
        tmp_file_path = tmp_file.name

    yield tmp_file_path

    # Cleanup
    if os.path.exists(tmp_file_path):
        os.unlink(tmp_file_path)


@pytest.fixture
def mock_endpoint():
    """Provide a mock endpoint URL for testing.

    Returns:
        str: Mock HTTP endpoint URL.
    """
    return "http://localhost:8000/events"
