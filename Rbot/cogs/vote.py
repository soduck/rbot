import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import re

EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

class Vote(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="vote", description="投票を開始します（例: 質問 | 選択肢1 | 選択肢2 | ... | time=30s）")
    async def vote(self, interaction: discord.Interaction, arg: str):
        time_seconds = 30  # デフォルト30秒

        # time=30s を抽出
        time_match = re.search(r'time=(\d+)([sm]?)', arg)
        if time_match:
            num = int(time_match.group(1))
            unit = time_match.group(2)
            if unit == "m":
                time_seconds = num * 60
            else:
                time_seconds = num
            arg = re.sub(r'\|?\s*time=\d+[sm]?', '', arg)

        parts = [x.strip() for x in arg.split("|") if x.strip()]
        if len(parts) < 3:
            await interaction.response.send_message("⚠️ フォーマット: `/vote 質問 | 選択肢1 | 選択肢2 | ... | time=30s`", ephemeral=True)
            return

        question = parts[0]
        choices = parts[1:]

        if len(choices) > len(EMOJIS):
            await interaction.response.send_message("⚠️ 選択肢は最大10個までです。", ephemeral=True)
            return

        description = ""
        for i, choice in enumerate(choices):
            description += f"{EMOJIS[i]} {choice}\n"

        embed = discord.Embed(
            title="🗳️ 投票",
            description=f"**{question}**\n\n{description}",
            color=0x00BFFF
        )
        embed.set_footer(text=f"{time_seconds}秒後に自動集計します。")

        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        for i in range(len(choices)):
            await message.add_reaction(EMOJIS[i])

        await asyncio.sleep(time_seconds)

        # 集計
        message = await interaction.channel.fetch_message(message.id)
        results = []
        for i in range(len(choices)):
            emoji = EMOJIS[i]
            for reaction in message.reactions:
                if str(reaction.emoji) == emoji:
                    count = reaction.count - 1  # botの分を除く
                    results.append((choices[i], count))

# 勝者を発表
sorted_results = sorted(results, key=lambda x: x[1], reverse=True)
result_text = "\n".join([f"{choice}：{count}票" for choice, count in sorted_results])

if sorted_results:
    top_score = sorted_results[0][1]
    top_choices = [choice for choice, count in sorted_results if count == top_score]
    if len(top_choices) == 1:
        winner_text = f"🏆 **最多得票：{top_choices[0]}**"
    else:
        winner_text = f"🤝 **引き分けです！**\n同票：{', '.join(top_choices)}"
else:
    winner_text = "⚠️ 投票がありませんでした。"

result_embed = discord.Embed(
    title="📊 投票結果",
    description=f"**{question}**\n\n{result_text}\n\n{winner_text}",
    color=0x2ECC71
)

        await interaction.followup.send(embed=result_embed)

async def setup(bot):
    await bot.add_cog(Vote(bot))

