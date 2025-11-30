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
	@echo "  make test            		Run tests inside Docker dev container"
	@echo "  make test_cluster    		Run cluster tests inside Docker dev container"
	@echo "  make test_all        		Run all tests inside Docker dev container"
	@echo "  make populate_cluster		Populate Redis cluster with test data"
	@echo "  make test_coverage   		Run tests with coverage report"
	@echo "  make coverage_html   		Generate HTML coverage report"
	@echo "  make publish         		Publish package to PyPI"
	@echo "  make docs            		Build documentation"
	@echo "  make docs_serve      		Serve documentation locally"
	@echo "  make docs_push       		Deploy documentation to GitHub Pages"
	@echo "  make docker_up       		Start all Docker services (dev, Redis, cluster)"
	@echo "  make docker_down     		Stop all Docker services and clean volumes"
	@echo "  make docker_shell    		Open shell in dev container"

clean:
	rm -rf build dist *.egg-info

build: clean
	python -m build

install_requirements:
	python -m pip install -r requirements.txt

install: install_requirements
	python -m pip install -e .

uninstall:
	python -m pip uninstall -y $(PACKAGE_NAME) || true

uninstall_all:
	python -m pip uninstall -y $(PACKAGE_NAME) || true
	python -m pip uninstall -y -r requirements.txt || true
	@echo "All packages in requirements.txt uninstalled"
	@echo "Note that some dependent packages may still be installed"
	@echo "To uninstall all packages, run 'pip freeze | xargs pip uninstall -y'"
	@echo "Do this at your own risk. Use a python virtual environment always."

test_install: build
	python -m pip uninstall -y $(PACKAGE_NAME) || true
	python -m pip install -e .
	python -c "import dj_redis_panel; print('✅ Import success!')"

test:
	@echo "Starting Docker services..."
	docker compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 10
	@echo "Running tests (excluding cluster tests) in dev container..."
	@docker compose exec dev bash -c "cd /app && REDIS_HOST=redis python -m pytest tests/ -m 'not cluster' -v"
	@echo "✅ Tests completed"

test_cluster:
	@echo "Starting Docker services..."
	@docker compose up -d
	@echo "Waiting for cluster to initialize..."
	@sleep 10
	@echo "Running cluster tests in dev container..."
	@docker compose exec dev bash -c "cd /app && REDIS_HOST=redis python -m pytest tests/ -m 'cluster' -v"
	@echo "✅ Cluster tests completed"

test_all:
	@echo "Starting Docker services..."
	@docker compose up -d
	@echo "Waiting for cluster to initialize..."
	@sleep 10
	@echo "Running all tests in dev container..."
	@docker compose exec dev bash -c "cd /app && REDIS_HOST=redis python -m pytest tests/ -v"
	@echo "✅ All tests completed"

test_coverage:
	@echo "Running tests with coverage"
	@docker compose up -d
	@echo "Waiting for cluster to initialize..."
	@sleep 10
	@echo "Running all tests in dev container..."
	@docker compose exec dev bash -c "cd /app && REDIS_HOST=redis python -m pytest --cov=dj_redis_panel --cov-report=xml --cov-report=html --cov-report=term-missing tests/"
	@echo "✅ All tests completed"

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

# Docker targets
docker_up:
	@echo "Starting all Docker services..."
	@docker compose up -d
	@echo "Waiting for cluster to initialize..."
	@sleep 10
	@echo "✅ All services are running:"
	@echo "   Dev container: dj-redis-panel-dev-1"
	@echo "   Standalone Redis: localhost:6379"
	@echo "   Cluster Node 0: localhost:7000"
	@echo "   Cluster Node 1: localhost:7001"
	@echo "   Cluster Node 2: localhost:7002"
	@echo ""
	@echo "Run 'make docker_shell' to open a shell in the dev container"

docker_down:
	@echo "Stopping all Docker services and cleaning volumes..."
	@docker compose down -v
	@echo "✅ All services stopped and volumes cleaned"

docker_shell:
	@echo "Opening shell in dev container..."
	@docker compose exec dev bash

populate_cluster:
	@echo "Starting Docker services..."
	@docker compose up -d
	@echo "Waiting for cluster to initialize..."
	@sleep 10
	@echo "Populating Redis cluster with test data..."
	@docker compose exec dev bash -c "cd /app/example_project && python manage.py populate_redis --instance redis-cluster --keys 50 --large-collections --large-collection-count 10 --max-collection-size 500"
	@echo "✅ Cluster populated with test data"
