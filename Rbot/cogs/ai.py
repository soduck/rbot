import discord
from discord.ext import commands
import openai

# ✅ OpenAI APIキーを直接記述
openai.api_key = "sk-WsTCuES0rdDz9tjkDqMHKBI0jMghO6jl2bHW1mb0xqT3BlbkFJDP9KKBVnE-YqKs-HU8ek0VmZCr19QFJaiBMjf8EhUA"

# ✅ ユーザーごとの会話履歴（文脈）を保持する辞書
user_histories = {}

class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ai(self, ctx, *, prompt: str = None):
        user_id = str(ctx.author.id)

        # メッセージが空だった場合
        if prompt is None:
            await ctx.send("❗メッセージが空です。`!ai メッセージ` または `!ai reset` を使ってください。")
            return

        # ✅ resetコマンド処理
        if prompt.strip().lower() == "reset":
            user_histories[user_id] = [
                {"role": "system", "content": "あなたは親切で賢いAIアシスタントです。"}
            ]
            await ctx.send("🧹 会話履歴をリセットしました！")
            return

        await ctx.send("🤖 ChatGPTに送信中...")

        # 履歴がなければ初期化
        if user_id not in user_histories:
            user_histories[user_id] = [
                {"role": "system", "content": "あなたは親切で賢いAIアシスタントです。"}
            ]

        # ユーザーの入力を履歴に追加
        user_histories[user_id].append({"role": "user", "content": prompt})

        try:
            # OpenAIへリクエスト
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=user_histories[user_id],
                max_tokens=150,
                temperature=0.7
            )

            # 応答を取得
            reply = response["choices"][0]["message"]["content"]

            # 応答を履歴に追加
            user_histories[user_id].append({"role": "assistant", "content": reply})

            # Discordへ送信
            await ctx.send(reply)

            # 長すぎる履歴はトリミング（20メッセージ以上なら切る）
            if len(user_histories[user_id]) > 20:
                user_histories[user_id] = user_histories[user_id][:1] + user_histories[user_id][-18:]

            # ターミナル出力（エンコード安全）
            try:
                print("🧠 応答: ", reply.encode('utf-8', errors='ignore'))
            except:
                pass

        except Exception as e:
            print(f"❌ エラー: {e}")
            await ctx.send("❌ エラーが発生しました。")

# 拡張機能として登録
async def setup(bot):
    await bot.add_cog(AIChat(bot))
