import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
import string
import re

class Survey(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.surveys = {}  # {passcode: {'question': str, 'answers': {}, 'guild_id': int, 'task': asyncio.Task}}

    def generate_passcode(self):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

    @app_commands.command(name="survey", description="アンケートを開始します")
    @app_commands.describe(question="質問内容", time="有効時間（例: 10s, 5m, 1h）", code="パスコード（省略可）")
    @app_commands.checks.has_permissions(administrator=True)
    async def survey(self, interaction: discord.Interaction, question: str, time: str = None, code: str = None):
        # 有効時間解析
        time_sec = None
        if time:
            match = re.match(r"(\d+)([smh]?)", time)
            if match:
                num, unit = match.groups()
                num = int(num)
                if unit == 'm':
                    num *= 60
                elif unit == 'h':
                    num *= 3600
                time_sec = num

        passcode = code if code else self.generate_passcode()

        if passcode in self.surveys:
            await interaction.response.send_message("❌ このパスコードは既に使用されています。別のコードを指定してください。", ephemeral=True)
            return

        self.surveys[passcode] = {'question': question, 'answers': {}, 'guild_id': interaction.guild.id}
        await interaction.response.send_message(
            f"📋 アンケート開始！\n**質問:** {question}\n\nDMで `!answer {passcode} <回答>` を送信して回答してください。\n（パスコード: `{passcode}`）",
            ephemeral=False
        )
        
        if time_sec:
            task = asyncio.create_task(self.end_survey_after(interaction, passcode, time_sec))
            self.surveys[passcode]['task'] = task

    async def end_survey_after(self, interaction, passcode, time_sec):
        await asyncio.sleep(time_sec)
        if passcode in self.surveys:
            await self.display_results(interaction, passcode)

    async def display_results(self, interaction, passcode):
        survey = self.surveys.pop(passcode)
        result_text = f"📊 アンケート結果（パスコード: {passcode}）\n**質問:** {survey['question']}\n\n"
        if survey['answers']:
            for uid, ans in survey['answers'].items():
                user = self.bot.get_user(uid)
                name = user.display_name if user else "Unknown"
                result_text += f"- **{name}:** {ans}\n"
        else:
            result_text += "回答はありませんでした。"
        guild = self.bot.get_guild(survey['guild_id'])
        if guild:
            channel = interaction.channel or guild.system_channel
            await channel.send(result_text)
        else:
            await interaction.followup.send(result_text)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not isinstance(message.channel, discord.DMChannel):
            return
        if message.content.startswith("!answer "):
            parts = message.content.split(maxsplit=2)
            if len(parts) < 3:
                await message.channel.send("❌ 正しい形式で入力してください。\n例: `!answer <パスコード> <回答>`")
                return
            passcode = parts[1]
            answer = parts[2]

            if passcode not in self.surveys:
                await message.channel.send("❌ 無効なパスコードです。")
                return

            survey = self.surveys[passcode]
            survey['answers'][message.author.id] = answer
            await message.channel.send(f"✅ アンケート（パスコード: {passcode}）に回答を受け付けました！")

    @app_commands.command(name="survey_results", description="アンケート結果を表示します")
    @app_commands.describe(passcode="パスコード")
    @app_commands.checks.has_permissions(administrator=True)
    async def survey_results(self, interaction: discord.Interaction, passcode: str):
        if passcode not in self.surveys:
            await interaction.response.send_message("❌ 指定されたパスコードのアンケートはありません。", ephemeral=True)
            return
        task = self.surveys[passcode].get('task')
        if task:
            task.cancel()
        await self.display_results(interaction, passcode)

async def setup(bot):
    await bot.add_cog(Survey(bot))
