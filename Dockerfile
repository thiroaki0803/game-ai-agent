FROM python:3.12

WORKDIR /app

COPY requirements.txt .
# 必要な依存関係をインストール
RUN apt-get update
RUN curl -fsSL https://ollama.com/install.sh | sh
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt
COPY ./app/ .

# CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8080"]