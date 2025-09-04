import discord
from discord.ext import commands
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta

NG_WORDS = [ "バカ", "カス", "荒らし","ちんぽ","ちんちん","うんこ","うんち","死","sex","オナニー","あなる","アナル","ちん","殺","呪う","うんぴ","馬鹿","ばか","baka","かす","荒らす","tinpo","tintin"]
SPAM_INTERVAL = 1  # 秒以内の連投をスパムと判定
SPAM_LIMIT = 2     # この回数を超えたらスパム
TIMEOUT_SECONDS = 180  # タイムアウト時間


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message_logs = defaultdict(list)  # user_id: [timestamp, ...]

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        user_id = message.author.id
        now = datetime.utcnow()

        # ✅ NGワードチェック
        lowered = message.content.lower()
        if any(word in lowered for word in NG_WORDS):
            await message.delete()
            await self._timeout_user(message.author, reason="NGワード")
            await message.channel.send(f"🚫 {message.author.mention} のメッセージはNGワードで削除されました。")
            return

        # ✅ スパム検知（一定時間内の連投）
        timestamps = self.message_logs[user_id]
        timestamps.append(now)
        self.message_logs[user_id] = [t for t in timestamps if (now - t).total_seconds() < SPAM_INTERVAL]

        if len(self.message_logs[user_id]) > SPAM_LIMIT:
            await self._timeout_user(message.author, reason="スパム検知")
            await message.channel.send(f"🔇 {message.author.mention} はスパム行為により一時ミュートされました。")
            self.message_logs[user_id] = []

    async def _timeout_user(self, user: discord.Member, reason: str):
        try:
            until = discord.utils.utcnow() + timedelta(seconds=TIMEOUT_SECONDS)
            await user.timeout(until, reason=reason)
        except Exception as e:
            print(f"❌ タイムアウト失敗: {e}")

async def setup(bot):
    await bot.add_cog(Moderation(bot))
