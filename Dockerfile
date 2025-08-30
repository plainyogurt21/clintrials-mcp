FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY mcp_server.py .
COPY manifest.json .
COPY package.json .

# Set transport mode to HTTP for container runtime
ENV TRANSPORT=http

CMD ["python", "mcp_server.py"]
