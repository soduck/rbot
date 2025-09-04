import discord
from discord.ext import commands
from discord import app_commands
import random
from cogs.stats_manager import StatsManager

stats = StatsManager()

class Janken(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.choices = ["グー", "チョキ", "パー"]

    @app_commands.command(name="janken", description="じゃんけんをします（グー / チョキ / パー）")
    async def janken(self, interaction: discord.Interaction, hand: str):
        user_hand = hand.strip()
        if user_hand not in self.choices:
            await interaction.response.send_message("❌ グー / チョキ / パー のいずれかを入力してください", ephemeral=True)
            return

        bot_hand = random.choice(self.choices)
        result = self.judge(user_hand, bot_hand)

        if result == "win":
            stats.record_result(interaction.user.id, "janken", "win")
            msg = f"🧠 僕の手: {bot_hand}\n🎉 あなたの勝ち！"
        elif result == "lose":
            stats.record_result(interaction.user.id, "janken", "lose")
            msg = f"🧠 僕の手: {bot_hand}\n😢 あなたの負け！"
        else:
            msg = f"🧠 僕の手: {bot_hand}\n🤝 あいこだね！"

        await interaction.response.send_message(msg)

    def judge(self, user, bot):
        if user == bot:
            return "draw"
        wins = {
            "グー": "チョキ",
            "チョキ": "パー",
            "パー": "グー"
        }
        return "win" if wins[user] == bot else "lose"

async def setup(bot):
    await bot.add_cog(Janken(bot))
