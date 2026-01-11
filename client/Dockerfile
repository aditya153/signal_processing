FROM python:3.11-slim

WORKDIR /client

# Copy and install requirements
COPY client/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY client/src ./src

# Run the script
CMD ["python", "src/signal_processing.py"]