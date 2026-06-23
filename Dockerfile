# Deployable image for the contract reviewer HTTP service.
# At runtime, point LLM_BASE_URL at a reachable OpenAI-compatible model server
# (e.g. an Ollama instance); no paid API key is required.
FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml ./
COPY contract_review ./contract_review
COPY evaluation ./evaluation
RUN pip install --no-cache-dir -e .

EXPOSE 8000
CMD ["uvicorn", "contract_review.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
