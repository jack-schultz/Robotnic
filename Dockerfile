FROM python:3.13.9-alpine AS base
WORKDIR /app

# install deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-topgg.txt --no-deps

# copy source
COPY . .

# cmd
CMD ["python", "main.py"]
