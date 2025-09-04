import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="play", description="検索ワードまたはURLから音楽を再生します")
    @app_commands.describe(query="曲名やアーティスト名（またはYouTubeのURL）")
    async def play(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer(thinking=True)
        print(f"/play 呼び出し: {query}")

        try:
            # BotがVCにいなければjoinする
            if interaction.guild.voice_client is None:
                if interaction.user.voice:
                    channel = interaction.user.voice.channel
                    await channel.connect()
                else:
                    await interaction.followup.send("❗ 先にVCに入ってから使ってね！", ephemeral=True)
                    return

            # YouTube検索 or URLから取得
        ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'noplaylist': True,
        'cookiefile': 'www.youtube.com_cookies.txt',  # ここでクッキーファイル指定
        }
 

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(query, download=False)
                # ytsearch時は 'entries' に複数入るので先頭を選ぶ
                if 'entries' in info:
                    info = info['entries'][0]
                stream_url = info['url']
                title = info.get("title", "Unknown Title")
                webpage_url = info.get("webpage_url", "")

                print(f"🎵 タイトル: {title}")
                print(f"🔗 再生ページ: {webpage_url}")
                print(f"▶️ ストリームURL: {stream_url}")

            # 音声ソース再生
            source = await discord.FFmpegOpusAudio.from_probe(stream_url)
            interaction.guild.voice_client.stop()
            interaction.guild.voice_client.play(source)

            await interaction.followup.send(
                f"🎶 再生中: **[{title}]({webpage_url})**"
            )

        except Exception as e:
            print(f"再生エラー: {e}")
            await interaction.followup.send("❌ 再生に失敗しました。検索語またはURLが正しいか確認してね。", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Music(bot))

