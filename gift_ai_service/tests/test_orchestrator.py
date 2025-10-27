"""
tests/test_orchestrator.py
--------------------------
Unit test for orchestrator integration pipeline.
"""

import pytest
from core.orchestrator import GiftOrchestrator

@pytest.mark.asyncio
async def test_generate_bundle_pipeline(mocker):
    """Basic integration test mock."""
    mock_llm = mocker.Mock()
    mock_vector = mocker.Mock()
    orch = GiftOrchestrator(mock_llm, mock_vector)
    result = await orch.generate_bundle_pipeline("Gift for mom under 2000")
    assert isinstance(result, dict)
