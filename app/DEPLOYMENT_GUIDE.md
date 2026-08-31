# Deployment

The public application is deployed as a Docker Space at:

<https://huggingface.co/spaces/yunqianz/purpleair-calibration>

The Space repository should contain the contents of this `app/` directory at
its root. Rename `README_HUGGINGFACE.md` to `README.md` in the Space so its
metadata selects `sdk: docker` and port 7860.

Required deployment files:

```text
README.md
Dockerfile
requirements.txt
app.py
sample_data.csv
.streamlit/config.toml
models/
utils/
```

The container health endpoint is `/_stcore/health`. A successful deployment
returns HTTP 200 from:

<https://yunqianz-purpleair-calibration.hf.space/_stcore/health>

## Local container check

```bash
docker build -t purpleair-calibration .
docker run --rm -p 7860:7860 purpleair-calibration
```

Open <http://localhost:7860> and run the packaged example before publishing.
