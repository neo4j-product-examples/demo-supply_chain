
FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
CMD ["uvicorn", "supply_chain_toolset:app", "--host", "0.0.0.0", "--port", "8080"]
