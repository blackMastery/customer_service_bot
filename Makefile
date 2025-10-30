.PHONY: help install run-api run-ui build-kb test docker-up docker-down clean

help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make run-api      - Run API server"
	@echo "  make run-ui       - Run Streamlit UI"
	@echo "  make build-kb     - Build knowledge base"
	@echo "  make test         - Run tests"
	@echo "  make docker-up    - Start Docker containers"
	@echo "  make docker-down  - Stop Docker containers"
	@echo "  make clean        - Clean generated files"

install:
	pip install -r requirements.txt
	cp .env.example .env
	@echo "Don't forget to edit .env with your API keys!"

run-api:
	python main.py

run-ui:
	streamlit run streamlit_app.py

build-kb:
	python build_knowledge_base.py build

test:
	pytest test_chatbot.py -v

test-cov:
	pytest test_chatbot.py --cov=. --cov-report=html

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage

setup: install build-kb
	@echo "Setup complete! Run 'make run-api' or 'make run-ui' to start."
