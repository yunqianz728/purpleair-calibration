# Tests

The maintained integration checks live beside the deployable application:

```bash
python app/test_calibration.py
```

GitHub Actions runs the integration pipeline, syntax checks, documentation
consistency checks, and a Streamlit smoke test for every push and pull request.
