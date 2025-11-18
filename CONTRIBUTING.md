# Contributing to PDF Extract with OCR

Thank you for your interest in contributing! This document provides guidelines for development.

## Development Setup

### 1. Clone the repository
```bash
git clone https://github.com/kjanat/pdf-extract-with-ocr.git
cd pdf-extract-with-ocr
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies (includes testing, linting, etc.)
pip install -r requirements-dev.txt
```

### 4. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 5. Initialize the database
```bash
python -c "from db import init_db; init_db()"
```

### 6. Install pre-commit hooks
```bash
pre-commit install
```

## Running the Application

### Local Development
```bash
python app.py
```

The application will be available at http://localhost:8080

### Docker Development
```bash
docker-compose up --build
```

## Testing

### Run all tests
```bash
pytest
```

### Run tests with coverage
```bash
pytest --cov
```

### Run specific test file
```bash
pytest tests/test_app.py
```

### Run specific test
```bash
pytest tests/test_app.py::test_upload_no_file
```

## Code Quality

### Format code with Black
```bash
black .
```

### Lint code with Ruff
```bash
ruff check .
```

### Fix linting issues automatically
```bash
ruff check --fix .
```

### Type checking with mypy
```bash
mypy .
```

## Pre-commit Hooks

Pre-commit hooks run automatically before each commit. They will:
- Format code with Black
- Lint code with Ruff
- Check for common issues (trailing whitespace, large files, etc.)
- Run type checking with mypy

To run pre-commit manually:
```bash
pre-commit run --all-files
```

## Pull Request Guidelines

1. **Create a feature branch** from `master`
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the code style guidelines

3. **Write or update tests** for your changes

4. **Run tests** and ensure they pass
   ```bash
   pytest
   ```

5. **Run code quality checks**
   ```bash
   black .
   ruff check .
   ```

6. **Commit your changes** with a descriptive message
   ```bash
   git add .
   git commit -m "Add feature: description"
   ```

7. **Push to your fork** and create a pull request

## Code Style

- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Write docstrings for all public functions and classes
- Keep functions focused and small (single responsibility)
- Maximum line length: 100 characters

## Testing Guidelines

- Write tests for all new features
- Maintain minimum 70% code coverage
- Use descriptive test names that explain what is being tested
- Use fixtures for common test setup
- Test both success and failure cases

## Documentation

- Update README.md if you change functionality
- Update API documentation if you add/modify endpoints
- Add docstrings to new functions and classes
- Update CHANGELOG.md for user-facing changes

## Questions?

Open an issue on GitHub if you have questions or need clarification.
