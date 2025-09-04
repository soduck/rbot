import discord
from discord.ext import commands
from discord import app_commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="commands", description="Botの利用可能なコマンド一覧を表示します")
    async def help_command(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🤖 Bot コマンド一覧",
            description="Botの利用可能なコマンドはこちら！",
            color=0x00BFFF
        )
        embed.add_field(
            name="🎮 ミニゲーム・AI",
            value="`/janken <手>` - じゃんけん勝負",
            inline=False
        )
        embed.add_field(
            name="📊 投票・タイマー",
            value="`/vote <質問 | 選択肢1 | 選択肢2 | ... | time=30s>` - 投票開始\n"
                  "`/timer <時間>` - タイマーセット（例: `10s`, `5m`）",
            inline=False
        )
        embed.add_field(
            name="🎵 音楽",
            value="`/join` - ボイスチャンネルに入る\n"
                  "`/leave` - ボイスチャンネルから抜ける\n"
                  "`/play <URL>` - 音楽を再生",
            inline=False
        )
        embed.add_field(
            name="📊 アンケート",
            value="`/survey <質問> | time=期間` - アンケート開始\n"
                  "`/answer Code <回答>` - アンケートに回答\n"
                  "`/survey_results Code` - アンケート終了、結果を表示",
            inline=False
        )
        embed.add_field(
            name="💰 経済",
            value="`/work` - ランダムにコインが獲得できる\n"
                  "`/casino <かけ額>` - お金でカジノできる\n"
                  "`/pay @<プレイヤー名> <金額>` - コインを送金",
            inline=False
        )
        embed.add_field(
            name="🛡️ モデレーション",
            value="不適切ワードやスパム対策は自動で行います\n"
                  "`/report @<名前> <理由>` - 通報",
            inline=False
        )
        embed.set_footer(text="お困りの場合はサーバー管理者にお問い合わせください。")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))
