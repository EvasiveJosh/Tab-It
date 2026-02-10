FROM python:3.11-slim

# Install system dependencies (ffmpeg required for audio-separator)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install PyTorch CPU build first (the +cpu tags in requirements.txt need the pytorch index)
RUN pip install --no-cache-dir \
    torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies from requirements.txt (skip torch lines, already installed above)
COPY requirements.txt .
RUN sed -i 's/\r$//' requirements.txt && \
    grep -aiv "^torch" requirements.txt > requirements_filtered.txt && \
    pip install --no-cache-dir -r requirements_filtered.txt && \
    rm requirements_filtered.txt
    
# Deployment dependencies
RUN pip install --no-cache-dir gunicorn

# Copy application code
COPY . .

# Create working directories
RUN mkdir -p uploads output_stems

EXPOSE 5000

# Use gunicorn with a single worker (ML model is memory-heavy)
# High timeout because audio separation can take a while
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "600", "--workers", "1", "audio_splitter:app"]


