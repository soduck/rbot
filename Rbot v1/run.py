from flask import Flask
from threading import Thread
import asyncio
import bot  # 既存の bot.py をインポート

app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=3000)

def start_flask():
    t = Thread(target=run)
    t.start()

if __name__ == "__main__":
    start_flask()
    asyncio.run(bot.main())  # bot.pyのmain関数呼び出し
