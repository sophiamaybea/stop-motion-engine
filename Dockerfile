FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -e . && pip install --no-cache-dir -r requirements-lab.txt
EXPOSE 7860
CMD ["python", "app/app.py"]
