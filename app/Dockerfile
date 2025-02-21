FROM python:3.12

WORKDIR /app

# Configure pip to use retries and increased timeout
RUN pip config set global.timeout 1000 && \
    pip config set global.retries 10

COPY ./requirements /app/requirements

# Install dependencies with additional retry flags
RUN pip install --no-cache-dir --retries 10 --timeout 1000 -r /app/requirements

# CMD fastapi run --reload
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--loop", "asyncio", "--reload"]