FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Where the .session file and sqlite db will live — mount this as a volume
VOLUME ["/app/data"]

CMD ["python3", "-u", "SecPhoto-docker.py"]