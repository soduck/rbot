import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import re

class Timer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="timer", description="タイマーをセットします（例: 10s, 2m）")
    async def timer(self, interaction: discord.Interaction, duration: str):
        # 入力チェック
        if not duration:
            await interaction.response.send_message("⏱ 使い方: `/timer 10s` または `/timer 2m`（s＝秒、m＝分）", ephemeral=True)
            return

        match = re.fullmatch(r'(\d+)([sm])', duration)
        if not match:
            await interaction.response.send_message("❌ フォーマットが間違っています。例: `10s`, `5m`", ephemeral=True)
            return

        amount, unit = int(match.group(1)), match.group(2)
        seconds = amount * 60 if unit == "m" else amount

        # タイマー開始メッセージ
        await interaction.response.send_message(f"⏳ タイマーを {amount}{unit} セットしました。時間が来たらお知らせします。")
        await asyncio.sleep(seconds)

        # タイマー終了メッセージ
        await interaction.followup.send(f"⏰ {interaction.user.mention} タイマー（{amount}{unit}）が終了しました！")

async def setup(bot):
    await bot.add_cog(Timer(bot))
