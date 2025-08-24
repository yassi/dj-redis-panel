PACKAGE_NAME = dj_redis_panel
PYPI_REPO ?= pypi   # can be 'testpypi' or 'pypi'

.PHONY: help clean build publish test install

help:
	@echo "Makefile targets:"
	@echo "  make clean           		Remove build artifacts"
	@echo "  make build           		Build sdist and wheel (in ./dist)"
	@echo "  make install_requirements 	Install all dev dependencies"
	@echo "  make install         		Install dependencies and package in editable mode"
	@echo "  make uninstall       		Uninstall package"
	@echo "  make uninstall_all   		Uninstall all packages"
	@echo "  make test_install    		Check if package can be imported"
	@echo "  make test            		Run tests"
	@echo "  make test_coverage   		Run tests with coverage report"
	@echo "  make coverage_html   		Generate HTML coverage report"
	@echo "  make publish         		Publish package to PyPI"
	@echo "  make docs            		Build documentation"
	@echo "  make docs_serve      		Serve documentation locally"
	@echo "  make docs_push       		Deploy documentation to GitHub Pages"

clean:
	rm -rf build dist *.egg-info

build: clean
	python -m build

install_requirements:
	pip install -r requirements.txt

install: install_requirements
	pip install -e .

uninstall:
	pip uninstall -y $(PACKAGE_NAME) || true

uninstall_all:
	pip uninstall -y $(PACKAGE_NAME) || true
	pip uninstall -y -r requirements.txt || true
	@echo "All packages in requirements.txt uninstalled"
	@echo "Note that some dependent packages may still be installed"
	@echo "To uninstall all packages, run 'pip freeze | xargs pip uninstall -y'"
	@echo "Do this at your own risk. Use a python virtual environment always."

test_install: build
	pip uninstall -y $(PACKAGE_NAME) || true
	pip install -e .
	python -c "import dj_redis_panel; print('✅ Import success!')"

test: install
	python -m pytest tests/

test_coverage: install
	pytest --cov=dj_redis_panel --cov-report=xml --cov-report=html --cov-report=term-missing

coverage_html: test_coverage
	@echo "Coverage report generated in htmlcov/index.html"
	@echo "Open htmlcov/index.html in your browser to view the detailed report"

publish:
	twine upload --repository $(PYPI_REPO) dist/*

docs: install
	mkdocs build

docs_serve: docs
	mkdocs serve

docs_push: docs
	mkdocs gh-deploy --force
