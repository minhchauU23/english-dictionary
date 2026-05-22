FROM python:3.12-slim

WORKDIR /usr/local/app

# IMPORTANT: fix Python buffering (tqdm + logs)
ENV PYTHONUNBUFFERED=1

# System deps
RUN apt-get update && apt-get install -y \
    default-mysql-client \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# App source
COPY . .

# Run ETL
CMD ["python", "init.py"]