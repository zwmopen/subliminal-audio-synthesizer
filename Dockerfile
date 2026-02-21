FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p uploads output logs test_audio

EXPOSE 5000

ENV FLASK_APP=subliminal_master.py
ENV PYTHONUNBUFFERED=1

CMD ["python", "subliminal_master.py"]
