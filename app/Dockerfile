FROM python:3.12

WORKDIR /app

COPY ./requirements /app/requirements

RUN pip install -r /app/requirements

# CMD fastapi run --reload
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--loop", "asyncio", "--reload"]