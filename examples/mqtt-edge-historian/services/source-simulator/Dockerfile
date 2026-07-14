FROM docker.io/library/python:3.12-slim

WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY app/ /app/

CMD ["python", "/app/publisher.py"]
