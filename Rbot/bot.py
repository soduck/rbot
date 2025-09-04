import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio

# .env 読み込み
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# インテント設定
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True  # スラッシュコマンド同期に必要

# Bot定義（コマンドプレフィックス指定は残してもOK）
bot = commands.Bot(command_prefix="!", intents=intents)

# 起動時イベント
@bot.event
async def on_ready():
    print(f"✅ {bot.user.name} がログインしました！")

    try:
        # スラッシュコマンドをグローバルに同期
        await bot.tree.sync()
        print("✅ スラッシュコマンドをグローバル同期しました！")
        
        # 即時反映したい場合（ギルド指定）
        # GUILD_ID = 123456789012345678  # 自分のサーバーIDに置き換え
        # await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        # print(f"✅ ギルド（ID={GUILD_ID}）にスラッシュコマンドを同期しました！")
    except Exception as e:
        print(f"❌ スラッシュコマンド同期失敗: {e}")

# 拡張機能読み込み
async def main():
    async with bot:
        cogs = [
            "cogs.music",
            "cogs.janken",
            "cogs.vote",
            "cogs.moderation",
            "cogs.timer",
            "cogs.help",
            "cogs.moderation_ext",
            "cogs.global_chat",
            "cogs.survey",
            "cogs.sinbun",
            "cogs.economy",
            "cogs.anaunsu",
            "cogs.todo"
        ]
        for cog in cogs:
            try:
                await bot.load_extension(cog)
                print(f"✅ {cog} 読み込み成功")
            except Exception as e:
                print(f"❌ {cog} 読み込み失敗: {e}")

        await bot.start(TOKEN)

# 実行
asyncio.run(main())
