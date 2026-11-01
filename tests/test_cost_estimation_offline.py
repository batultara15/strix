"""Cost estimates must use local pricing data without triggering provider login."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import litellm
import pytest

from strix.report.pricing import resolve_litellm_model
from strix.report.state import _estimate_response_cost
from strix.report.usage import _estimate_litellm_entry_cost


@pytest.mark.parametrize("path", ["callback", "ledger"])
def test_cost_estimate_never_discovers_provider(path: str, monkeypatch: pytest.MonkeyPatch) -> None:
    model = "github_copilot/strix-offline-pricing"
    monkeypatch.setattr(
        litellm,
        "model_cost",
        {
            model: {
                "litellm_provider": "github_copilot",
                "mode": "chat",
                "input_cost_per_token": 0.001,
                "output_cost_per_token": 0.002,
                "max_tokens": 4096,
            }
        },
    )
    discover = Mock(side_effect=AssertionError("local pricing must not discover or authenticate"))
    monkeypatch.setattr(litellm, "get_llm_provider", discover)
    resolve_litellm_model.cache_clear()
    try:
        if path == "callback":
            cost = _estimate_response_cost(
                {"model": model},
                {"usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}},
            )
        else:
            usage = SimpleNamespace(input_tokens=10, output_tokens=5, total_tokens=15)
            cost = _estimate_litellm_entry_cost(usage, model)
        assert cost == pytest.approx(0.02)
        discover.assert_not_called()
    finally:
        resolve_litellm_model.cache_clear()
