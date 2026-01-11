FROM python:3.10-slim

# Install system-level dependencies for running browsers
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PYTHONPATH=/app

# Copy requirements and install
COPY requirements_hf.txt .
RUN pip install --no-cache-dir -r requirements_hf.txt

# Install Playwright browser and its system dependencies
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy application code
COPY . .

# Hugging Face Spaces usually uses port 7860
EXPOSE 7860

# Run the app
CMD ["uvicorn", "hf_app:app", "--host", "0.0.0.0", "--port", "7860"]
