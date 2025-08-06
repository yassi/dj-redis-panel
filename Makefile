PACKAGE_NAME = dj_redis_admin
PYPI_REPO ?= pypi   # can be 'testpypi' or 'pypi'

.PHONY: help clean build publish test install

help:
	@echo "Makefile targets:"
	@echo "  make clean        – Remove build artifacts"
	@echo "  make build        – Build sdist and wheel (in ./dist)"
	@echo "  make publish      – Upload to PyPI (default) or TestPyPI"
	@echo "  make install      – Install package locally via pip"
	@echo "  make test         – Install from dist and run smoke test"
	@echo "  make help         – Show this help message"

clean:
	rm -rf build dist *.egg-info

build:
	python -m build

publish: build
	twine upload --repository $(PYPI_REPO) dist/*

install:
	pip install -e .

test:
	pip uninstall -y $(PACKAGE_NAME) || true
	pip install dist/*.whl
	python -c "import dj_redis_admin; print('✅ Import success!')"
