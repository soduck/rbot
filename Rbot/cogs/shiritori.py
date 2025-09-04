import discord
from discord.ext import commands
import openai

# ✅ OpenAI APIキーを直接設定（v0.28系用）
openai.api_key = "sk-WsTCuES0rdDz9tjkDqMHKBI0jMghO6jl2bHW1mb0xqT3BlbkFJDP9KKBVnE-YqKs-HU8ek0VmZCr19QFJaiBMjf8EhUA"

# ユーザーごとのセッション保存
shiritori_sessions = {}

class Shiritori(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def shiritori(self, ctx, *, word: str):
        user_id = str(ctx.author.id)
        word = word.strip()

        # ✅ 「ん or ン」で終わったらユーザーの負け
        if word.endswith("ん") or word.endswith("ン"):
            await ctx.send("❌『ん』または『ン』がついたのであなたの負けです！")
            shiritori_sessions.pop(user_id, None)
            return

        prompt = (
            f"しりとりをしましょう。前の単語は「{word}」です。\n"
            "その単語の最後の文字から始まる単語をひらがなで1つ返してください。\n"
            "返答はひらがな1単語のみ。「ん」で終わる単語は禁止です。"
        )

        await ctx.trigger_typing()

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "あなたはしりとりが得意なAIです。ひらがな1語だけ返してください。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=30,
                temperature=0.7,
            )

            ai_word = response["choices"][0]["message"]["content"].strip()

            if ai_word.endswith("ん") or ai_word.endswith("ン"):
                await ctx.send(f"🧠 {ai_word}…『ん』がついたので私の負けです！あなたの勝ち！🎉")
                shiritori_sessions.pop(user_id, None)
            else:
                shiritori_sessions[user_id] = ai_word
                await ctx.send(f"🧠 {ai_word}")

        except Exception as e:
            # 💡 エラーを ASCII で安全に表示
            print("❌ エラー内容（ASCII）:", str(e).encode('ascii', errors='replace').decode())
            await ctx.send("❌ ChatGPTとの通信中にエラーが発生しました。")

    @commands.command()
    async def shiritori_reset(self, ctx):
        user_id = str(ctx.author.id)
        if user_id in shiritori_sessions:
            del shiritori_sessions[user_id]
            await ctx.send("🔁 セッションをリセットしました。")
        else:
            await ctx.send("⚠️ セッションはまだ開始されていません。")

async def setup(bot):
    await bot.add_cog(Shiritori(bot))
