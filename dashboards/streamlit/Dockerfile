FROM python:3.11-slim
WORKDIR /app
COPY app.py /app/
RUN pip install streamlit sqlalchemy pandas psycopg2-binary
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
