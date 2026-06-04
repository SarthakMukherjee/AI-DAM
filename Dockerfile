FROM python:3.10-slim

WORKDIR /code

# Install system dependencies required for OpenCV, Pytesseract, and FFmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    tesseract-ocr \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from your backend folder and install them
COPY ./backend/requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy everything else into the container
COPY . .

# Tell Python to include the backend folder when looking for imports
ENV PYTHONPATH=/code/backend

# Run the super admin seeding script as a module, then start your FastAPI server
CMD python -m backend.app.db.seed.create_super_admin && uvicorn backend.app.main:app --host 0.0.0.0 --port 7860