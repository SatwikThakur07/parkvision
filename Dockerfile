FROM python:3.10-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements_integrated.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements_integrated.txt

# Copy source
COPY . .

# Expose API port
EXPOSE 8000

# Default command
CMD ["python", "run_integrated.py"]