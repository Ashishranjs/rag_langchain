FROM python:3.10-slim-bullseye

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

CMD ["python", "app.py"]


WORKDIR /app

# System dependencies required by sentence-transformers / torch
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first (better caching)
COPY requirements.txt .

# Upgrade pip and install deps
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy application code
COPY . .

CMD ["python", "app.py"]
