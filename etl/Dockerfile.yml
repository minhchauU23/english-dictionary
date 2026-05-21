FROM python:3.12-slim

WORKDIR /usr/local/app

# Install mysql client (mysqldump)
RUN apt-get update && apt-get install -y \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Run ETL
CMD ["python", "init.py"]