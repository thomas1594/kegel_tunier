FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Ensure the data directory exists (mounted as a volume at runtime)
RUN mkdir -p /app/data

# Expose Streamlit port
EXPOSE 8501

# Health check without curl (not present in the slim image)
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://localhost:8501/_stcore/health').status == 200 else 1)"

# Run streamlit
CMD ["streamlit", "run", "kegel.py", "--server.port=8501", "--server.address=0.0.0.0"]
