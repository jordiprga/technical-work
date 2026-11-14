"""Exercise rendering, recorded-artifact loading, and a real small training run."""
import json
from pathlib import Path

import pytest

pytest.importorskip("streamlit")
pytest.importorskip("plotly")
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_dashboard_empty_state():
    app = AppTest.from_file(str(APP), default_timeout=20).run()
    assert not app.exception
    assert app.title[0].value == "Entropy Oracle"
    assert any(item.label == "Entrenar y evaluar" for item in app.button)


def test_dashboard_renders_saved_measurements():
    app = AppTest.from_file(str(APP), default_timeout=20)
    app.session_state["oracle_result"] = {
        "config": {"source": "bernoulli", "seed": 123, "n": 500},
        "source_metadata": {"test_fixture": True},
        "metrics": [{"model": "marginal", "accuracy": .75, "log_loss_bits": .8,
                     "success_ci_low": .6, "success_ci_high": .9, "fit_seconds": .01}],
        "selection": {"selected_model": "marginal", "ensemble_weights": {"marginal": 1.0}},
        "trace": {"indices": [400, 401, 402, 403], "y": [0, 1, 1, 1],
                  "probabilities": {"marginal": [[.25, .75]] * 4}},
        "histories": {"marginal": []}, "comparisons": [],
    }
    app.run()
    assert not app.exception
    assert len(app.metric) == 4
    assert app.metric[2].value == "75.00%"


def test_dashboard_runs_real_small_experiment():
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    app.selectbox[0].set_value("bernoulli")
    app.number_input[0].set_value(500)
    app.multiselect[0].set_value(["marginal"])
    next(button for button in app.button if button.label == "Entrenar y evaluar").click().run()
    assert not app.exception
    assert not app.error
    result = app.session_state["oracle_result"]
    assert result["config"]["source"] == "bernoulli"
    assert result["split"]["test_count"] == 100
    assert result["metrics"][0]["trained"]


def test_dashboard_loads_real_nested_experiment():
    artifact = APP.parent / "results" / "main" / "nonlinear_seed11_n12000.json"
    if not artifact.exists():
        pytest.skip("Run the reproducible main experiment to populate saved artifacts.")
    expected = json.loads(artifact.read_text())
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    chooser = next(widget for widget in app.selectbox if widget.label == "Experimento")
    assert chooser.value == artifact  # The principal experiment is the default.
    assert "main/nonlinear_seed11_n12000.json" in chooser.options
    assert not any("simultaneous_comparisons" in name for name in chooser.options)
    chooser.set_value(artifact)
    next(button for button in app.button if button.label == "Abrir resultado").click().run()
    assert not app.exception
    assert not app.error
    result = app.session_state["oracle_result"]
    assert result["metrics"] == expected["metrics"]
    assert result["config"]["source"] == "nonlinear"
    assert result["config"]["seed"] == 11
    assert len(app.metric) == 4
