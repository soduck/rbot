# Pythonの軽量イメージを使う
FROM python:3.12-slim

# 作業ディレクトリを設定
WORKDIR /app

# 必要なパッケージをインストール
RUN apt update && \
    apt install -y ffmpeg curl && \
    apt clean

# 必要なPythonパッケージをインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションのコードとクッキーをコピー
COPY . .

# ポートは不要（外部公開しないBot）
CMD ["python", "bot.py"]
