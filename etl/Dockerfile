FROM python:3.11-slim
WORKDIR /app
COPY etl/ /app/etl
RUN pip install --no-cache-dir pandas sqlalchemy openpyxl click
ENTRYPOINT ["python", "-m", "etl.main"]
