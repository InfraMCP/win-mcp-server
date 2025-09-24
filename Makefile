.PHONY: install test format lint clean build upload

install:
	pip install -e ".[dev]"

test:
	pytest tests/

format:
	black src/ tests/
	isort src/ tests/

lint:
	black --check src/ tests/
	isort --check-only src/ tests/

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	python -m build

upload: build
	twine upload dist/*
