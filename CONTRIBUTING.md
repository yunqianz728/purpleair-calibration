# Contributing to PurpleAir Temperature Sensor Calibration

Thank you for your interest in contributing to this project! We welcome contributions from the community to improve the calibration framework, extend functionality, and enhance documentation.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Areas for Contribution](#areas-for-contribution)

## Code of Conduct

This project adheres to a code of conduct that all contributors are expected to follow. Please be respectful, inclusive, and professional in all interactions.

### Our Standards
- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## How Can I Contribute?

### Reporting Bugs
Before creating a bug report:
1. Check the [FAQ](docs/FAQ.md) and [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
2. Search existing [GitHub Issues](https://github.com/yourusername/purpleair-calibration/issues) to avoid duplicates
3. Verify the bug with the latest version of the code

When submitting a bug report, include:
- A clear, descriptive title
- Detailed steps to reproduce the issue
- Expected vs. actual behavior
- Your environment (OS, Python version, package versions)
- Code snippets and error messages
- Screenshots if applicable

### Suggesting Enhancements
Enhancement suggestions are tracked as GitHub Issues. When suggesting an enhancement:
- Use a clear, descriptive title
- Provide a detailed description of the proposed functionality
- Explain why this enhancement would be useful
- Include examples of how it would be used

### Contributing Code
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following our coding standards
4. Add tests for new functionality
5. Ensure all tests pass
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Development Setup

### Prerequisites
- Python 3.8 or higher
- Git
- conda (recommended) or pip

### Setup Steps
```bash
# Clone your fork
git clone https://github.com/yourusername/purpleair-calibration.git
cd purpleair-calibration

# Add upstream remote
git remote add upstream https://github.com/original/purpleair-calibration.git

# Create development environment
conda env create -f environment.yml
conda activate purpleair-calib

# Install in editable mode with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=models --cov=data --cov-report=html

# Run specific test file
pytest tests/test_features.py

# Run tests in parallel
pytest -n auto
```

## Coding Standards

### Python Style Guide
We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with some modifications:
- Line length: 100 characters (soft limit), 120 (hard limit)
- Use Black for automatic formatting
- Use type hints for function signatures
- Write docstrings in Google style

### Example Function
```python
from typing import Tuple
import pandas as pd
import numpy as np


def calculate_temperature_error(
    sensor_temp: pd.Series,
    reference_temp: pd.Series,
    weights: np.ndarray = None
) -> Tuple[float, float]:
    """Calculate weighted mean absolute error and RMSE for temperature predictions.

    Args:
        sensor_temp: Temperature readings from PurpleAir sensor (°C)
        reference_temp: Reference temperature from quality-controlled station (°C)
        weights: Optional sample weights for spatial similarity. If None,
            uniform weights are used.

    Returns:
        Tuple containing:
            - mae: Weighted mean absolute error (°C)
            - rmse: Weighted root mean squared error (°C)

    Raises:
        ValueError: If sensor_temp and reference_temp have different lengths

    Example:
        >>> sensor = pd.Series([25.5, 26.0, 24.8])
        >>> reference = pd.Series([23.0, 23.5, 22.5])
        >>> mae, rmse = calculate_temperature_error(sensor, reference)
        >>> print(f"MAE: {mae:.2f}°C, RMSE: {rmse:.2f}°C")
        MAE: 2.50°C, RMSE: 2.52°C
    """
    if len(sensor_temp) != len(reference_temp):
        raise ValueError("Sensor and reference data must have same length")

    if weights is None:
        weights = np.ones(len(sensor_temp))

    errors = sensor_temp - reference_temp
    mae = np.average(np.abs(errors), weights=weights)
    rmse = np.sqrt(np.average(errors**2, weights=weights))

    return mae, rmse
```

### Code Quality Tools
We use the following tools to maintain code quality:
- **Black**: Code formatting (`black .`)
- **Flake8**: Linting (`flake8 --max-line-length=120`)
- **MyPy**: Type checking (`mypy --ignore-missing-imports .`)
- **isort**: Import sorting (`isort .`)

Run all quality checks:
```bash
# Format code
black .
isort .

# Check for issues
flake8 --max-line-length=120
mypy --ignore-missing-imports models/ data/
```

### Documentation Standards
- All public functions/classes must have docstrings
- Use Google-style docstrings
- Include type hints
- Provide usage examples for complex functions
- Update README.md if adding new features
- Add inline comments for non-obvious logic

### Commit Message Guidelines
Follow conventional commits format:
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code formatting (no logic change)
- `refactor`: Code restructuring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Example**:
```
feat(models): Add CatBoost hyperparameter optimization

Implement Bayesian optimization for CatBoost models using Optuna.
Added 20-trial search over learning rate, depth, and regularization.

Closes #42
```

## Testing

### Test Structure
```
tests/
├── test_data_processing.py    # Data download and matching
├── test_features.py            # Feature engineering
├── test_models.py              # Model training and prediction
├── test_calibration.py         # End-to-end calibration
└── fixtures/                   # Test data fixtures
```

### Writing Tests
```python
import pytest
import pandas as pd
from models.calibration import TemporalTempStratCalibrator


@pytest.fixture
def sample_sensor_data():
    """Create sample sensor data for testing."""
    return pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=100, freq='H'),
        'temperature': 25.0 + np.random.randn(100) * 2.0,
        'humidity': 50.0 + np.random.randn(100) * 10.0,
        'latitude': 40.0,
        'longitude': -120.0,
        'elevation': 100.0
    })


def test_calibrator_initialization():
    """Test that calibrator initializes without errors."""
    calibrator = TemporalTempStratCalibrator()
    assert calibrator is not None
    assert hasattr(calibrator, 'models')


def test_calibration_reduces_error(sample_sensor_data):
    """Test that calibration reduces temperature error."""
    calibrator = TemporalTempStratCalibrator()

    # Add mock reference temperature
    sample_sensor_data['reference_temp'] = sample_sensor_data['temperature'] - 5.0

    calibrated = calibrator.calibrate(sample_sensor_data)

    original_mae = abs(sample_sensor_data['temperature'] -
                      sample_sensor_data['reference_temp']).mean()
    calibrated_mae = abs(calibrated['temperature_calibrated'] -
                        sample_sensor_data['reference_temp']).mean()

    assert calibrated_mae < original_mae, "Calibration should reduce MAE"
```

### Test Coverage Requirements
- Minimum 80% coverage for new code
- All public functions must have tests
- Test edge cases and error conditions
- Include integration tests for critical workflows

## Pull Request Process

### Before Submitting
1. Ensure all tests pass (`pytest`)
2. Run code quality checks (`black`, `flake8`, `mypy`)
3. Update documentation if needed
4. Add entry to CHANGELOG.md (if applicable)
5. Rebase on latest `main` branch

### PR Checklist
- [ ] Code follows project style guidelines
- [ ] All tests pass
- [ ] New tests added for new functionality
- [ ] Documentation updated
- [ ] Commit messages follow conventional commits
- [ ] No merge conflicts
- [ ] PR title clearly describes changes

### Review Process
1. Maintainers will review your PR within 1 week
2. Address any requested changes
3. Once approved, a maintainer will merge your PR
4. Your contribution will be acknowledged in release notes

## Areas for Contribution

### High Priority
- **Multi-platform support**: Extend calibration to Netatmo, Ambient Weather, Davis Instruments
- **Real-time data integration**: Connect to NOAA HRRR, ECMWF IFS for near-real-time calibration
- **Edge device optimization**: Port models to Raspberry Pi, Arduino for on-device calibration
- **GPU acceleration**: Optimize training for CUDA-enabled systems

### Medium Priority
- **Additional algorithms**: Implement neural networks, Gaussian processes
- **Uncertainty quantification**: Add prediction intervals and confidence bounds
- **Spatial interpolation**: Kriging-based temperature field reconstruction
- **Mobile app**: iOS/Android app for citizen scientists

### Documentation
- Tutorial notebooks for common use cases
- Video walkthroughs
- API reference improvements
- Troubleshooting guides for specific issues

### Testing
- More comprehensive integration tests
- Performance benchmarks
- Data validation tests
- Cross-platform compatibility tests

### Infrastructure
- Continuous integration/deployment (CI/CD)
- Docker containerization
- Cloud deployment guides (AWS, Google Cloud, Azure)
- Database integration for large-scale deployments

## Questions?

If you have questions about contributing:
- Open a [GitHub Discussion](https://github.com/yourusername/purpleair-calibration/discussions)
- Email the maintainers: lianglu@berkeley.edu
- Check existing documentation in the `docs/` folder

## Recognition

All contributors will be acknowledged in:
- CONTRIBUTORS.md file
- Release notes
- Paper acknowledgments (for substantial contributions)

Thank you for helping improve PurpleAir temperature calibration!
