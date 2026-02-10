FROM python:3.11-slim

WORKDIR /app

# Install dependencies from requirements.txt (filter out Windows-only packages)
COPY requirements.txt .
RUN grep -iv "tensorflow-intel\|tensorflow-io-gcs-filesystem" requirements.txt > requirements_filtered.txt && \
    pip install --no-cache-dir -r requirements_filtered.txt && \
    rm requirements_filtered.txt
RUN pip install --no-cache-dir gunicorn

# Copy application code
COPY . .

# Create working directories
RUN mkdir -p uploads midi_output

EXPOSE 5000

# Use gunicorn; high timeout for ML inference (basic-pitch)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "300", "--workers", "1", "app:app"]


