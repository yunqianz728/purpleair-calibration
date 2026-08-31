# Contributing

Thank you for helping improve the PurpleAir temperature calibration project.
Contributions to the web workflow, documentation, tests, and reproducibility
materials are welcome.

## Report a problem

Open a [GitHub issue](https://github.com/yunqianz728/purpleair-calibration/issues)
and include:

- a short description of the expected and observed behavior;
- a minimal, de-identified CSV when the problem is data-dependent;
- the operating system and Python version for local failures; and
- the full error message or a screenshot with sensitive information removed.

Please read the [FAQ](docs/FAQ.md) before filing an issue. Security-sensitive
reports should follow [SECURITY.md](SECURITY.md).

## Development setup

The maintained user-facing software is the Streamlit application in `app/`.

```bash
git clone https://github.com/yunqianz728/purpleair-calibration.git
cd purpleair-calibration/app
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

On Windows PowerShell, activate the environment with
`.venv\\Scripts\\Activate.ps1`.

## Tests

Run the integration checks from the repository root:

```bash
python app/test_calibration.py
python -m py_compile app/app.py app/utils/feature_engineering.py app/utils/model_predictor.py
```

Pull requests should keep both commands passing. New behavior should include a
focused test or a reproducible example.

## Pull requests

1. Create a branch from `main`.
2. Keep changes focused and document any scientific assumption.
3. Preserve row-level model provenance in calibrated downloads.
4. Update the README or usage guide when user-facing behavior changes.
5. Confirm that paper-model claims remain consistent with the final manuscript.
6. Open a pull request describing the change and the validation performed.

Do not commit API keys, credentials, identifiable sensor-owner information, or
large source datasets. Use the existing Zenodo records for archived research
data and models.

Participation is governed by the [Code of Conduct](CODE_OF_CONDUCT.md).
