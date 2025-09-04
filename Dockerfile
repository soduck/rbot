FROM python:3.12-slim

# ffmpegをインストール
RUN apt update && apt install -y ffmpeg

# 作業ディレクトリを指定
WORKDIR /app

# Rbot V1フォルダの中身をコピー
COPY ./Rbot V1 /app

# ライブラリインストール
RUN pip install --no-cache-dir -r requirements.txt

# Bot起動
CMD ["python", "bot.py"]
