PACKAGE_NAME = dj_redis_panel
PYPI_REPO ?= pypi   # can be 'testpypi' or 'pypi'

.PHONY: help clean build publish test install

help:
	@echo "Makefile targets:"
	@echo "  make clean        	    Remove build artifacts"
	@echo "  make build        		Build sdist and wheel (in ./dist)"
	@echo "  make install        	Install package locally via wheel"
	@echo "  make uninstall      	Uninstall package wheel package"
	@echo "  make install_dev    	Install package and all dev dependencies"
	@echo "  make test_install   	Check if package can be imported"
	@echo "  make test           	Run tests"
	@echo "  make publish        	Publish package to PyPI"

clean:
	rm -rf build dist *.egg-info

build:
	python -m build

install: build
	pip install dist/*.whl

uninstall:
	pip uninstall -y $(PACKAGE_NAME) || true

install_dev: build
	pip install -r requirements.txt

test_install: build
	pip uninstall -y $(PACKAGE_NAME) || true
	pip install dist/*.whl
	python -c "import dj_redis_panel; print('✅ Import success!')"

test: install_dev
	python -m pytest tests/

publish: build
	twine upload --repository $(PYPI_REPO) dist/*
