FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN sed -i 's/\r$//' requirements.txt && \
    pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn

# Copy application code
COPY . .

# Create working directories
RUN mkdir -p uploads midi_output

EXPOSE 5000

# timeout must exceed the auto-separator's timeout
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "1800", "--graceful-timeout", "1800", "--workers", "1", "app:app"]


