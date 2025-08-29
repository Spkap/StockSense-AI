FROM python:3.10-slim

# Install supervisor and system dependencies
RUN apt-get update && \
    apt-get install -y supervisor && \
    rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy requirements files
COPY requirements-backend.txt requirements-backend.txt
COPY requirements-frontend.txt requirements-frontend.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-backend.txt && \
    pip install --no-cache-dir -r requirements-frontend.txt

# Copy application code
COPY . /app

# Copy supervisord.conf
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose FastAPI and Streamlit ports
EXPOSE 8000
EXPOSE 7860

# Start supervisor
CMD ["supervisord", "-n"]
