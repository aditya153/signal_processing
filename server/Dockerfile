FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive 
RUN apt-get update && apt-get install netcat-traditional

COPY server /server
WORKDIR /server
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt
CMD echo "Server starting..." && python src/server.py