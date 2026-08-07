FROM docker.io/library/python:3.12-slim-bookworm

WORKDIR /srv/www
COPY static/ ./

USER 65532:65532
EXPOSE 8080

CMD ["python", "-m", "http.server", "8080", "--bind", "0.0.0.0"]
