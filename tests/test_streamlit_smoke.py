"""Smoke tests for the maintained Streamlit interface."""

from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_FILE = Path(__file__).resolve().parents[1] / "app" / "app.py"


def test_app_loads_with_expected_workflows():
    app = AppTest.from_file(str(APP_FILE)).run(timeout=60)
    assert not app.exception
    assert [tab.label for tab in app.tabs] == [
        "Calibrate data",
        "Working example",
        "Method & limits",
    ]
    assert "0.813°C held-out MAE" in app.info[0].value


def test_working_example_completes():
    app = AppTest.from_file(str(APP_FILE)).run(timeout=60)
    button = next(item for item in app.button if item.label == "Run working example")
    button.click().run(timeout=60)
    assert not app.exception
    assert any(metric.label == "Readings calibrated" and metric.value == "24" for metric in app.metric)
