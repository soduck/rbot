import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime
import json
import aiofiles
import asyncio
import os

# サーバーIDとチャンネルIDを設定
SERVER_ID = 1375003246229192744
CHANNEL_ID = 1375128818242818058

# 新聞データ保存先パス
DATA_PATH = os.path.join("data", "newspapers.json")
os.makedirs("data", exist_ok=True)  # データディレクトリ作成

class Newspaper(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.typing_task.start()

    @commands.Cog.listener()
    async def on_ready(self):
        # スラッシュコマンドをギルドに即同期
        await self.bot.tree.sync(guild=discord.Object(id=SERVER_ID))
        print(f"{self.bot.user} が起動しました。スラッシュコマンド同期完了！")

    @tasks.loop(seconds=15)
    async def typing_task(self):
        try:
            channel = await self.bot.fetch_channel(CHANNEL_ID)
            async with channel.typing():
                await asyncio.sleep(5)
        except Exception as e:
            print(f"typing_task エラー: {e}")

    @app_commands.command(name="shuukansi", description="新聞を創刊します")
    async def shuukansi(self, interaction: discord.Interaction, color: str, name: str, image: discord.Attachment):
        # 色定義
        COLORS = {"赤": 16711680, "黄": 16776960, "緑": 65280, "灰": 8421504}

        # 色が正しいかチェック
        if color not in COLORS:
            await interaction.response.send_message("❌ 色は「赤」「黄」「緑」「灰」から選んでください。", ephemeral=True)
            return

        color_code = COLORS[color]

        # 添付画像のURL取得（人画像対応修正）
        image_url = image.url

        # JSONファイルからデータ読み込み
        try:
            async with aiofiles.open(DATA_PATH, "r", encoding="utf-8_sig") as f:
                contents = await f.read()
                if contents:
                    data = json.loads(contents)
                else:
                    data = {}
        except Exception as e:
            print(f"JSON読み込みエラー: {e}")
            data = {}

        # 新聞データ保存
        data[name] = {
            "color": color_code,
            "creator_id": interaction.user.id
        }

        # JSONファイルにデータ書き込み
        try:
            async with aiofiles.open(DATA_PATH, "w", encoding="utf-8_sig") as f:
                await f.write(json.dumps(data, indent=4, ensure_ascii=False))
        except Exception as e:
            print(f"JSON書き込みエラー: {e}")

        # Embed作成
        embed = discord.Embed(
            title=f"{name}新聞創刊！",
            color=color_code,
            timestamp=datetime.datetime.now()
        )
        embed.set_image(url=image_url)
        embed.set_footer(text=f"{interaction.user.display_name}/総合新聞社")

        # チャンネルに投稿
        try:
            channel = await interaction.client.fetch_channel(CHANNEL_ID)
            await channel.send(embed=embed)
            await interaction.response.send_message(f"✅ {name}新聞を創刊しました！", ephemeral=True)
        except Exception as e:
            print(f"創刊エラー: {e}")
            await interaction.response.send_message(f"❌ エラーが発生しました: {e}", ephemeral=True)

    @app_commands.command(name="adddsec", description="新聞に記事を追加します")
    async def adddsec(self, interaction: discord.Interaction, name: str, article: str, image: discord.Attachment):
        # 添付画像のURL取得
        image_url = image.url

        # JSONファイルからデータ読み込み
        try:
            async with aiofiles.open(DATA_PATH, "r", encoding="utf-8_sig") as f:
                contents = await f.read()
                if contents:
                    data = json.loads(contents)
                else:
                    data = {}
        except Exception as e:
            print(f"JSON読み込みエラー: {e}")
            data = {}

        # 新聞存在確認
        if name not in data:
            await interaction.response.send_message(f"❌ {name}新聞が存在しません。先に /shuukansi で創刊してください。", ephemeral=True)
            return

        # 創刊者確認
        creator_id = data[name].get("creator_id")
        if interaction.user.id != creator_id:
            await interaction.response.send_message("❌ あなたはこの新聞の創刊者ではないため、記事を追加できません。", ephemeral=True)
            return

        # 新聞の色を取得
        color_code = data[name]["color"]

        # Embed作成（記事追加用）
        embed = discord.Embed(
            title=f"{name}新聞配布",
            description=article,
            color=color_code,
            timestamp=datetime.datetime.now()
        )
        embed.set_image(url=image_url)
        embed.set_footer(text=f"{interaction.user.display_name}/総合新聞社")

        # チャンネルに投稿・リアクション・スレッド作成
        try:
            channel = await interaction.client.fetch_channel(CHANNEL_ID)
            send_message = await channel.send(embed=embed)
            await send_message.add_reaction("👍")
            await send_message.add_reaction("👎")
            await send_message.create_thread(name="読者投稿欄")
            await interaction.response.send_message(f"✅ {name}新聞を配布しました！", ephemeral=True)
        except Exception as e:
            print(f"記事追加エラー: {e}")
            await interaction.response.send_message(f"❌ エラーが発生しました: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Newspaper(bot))
