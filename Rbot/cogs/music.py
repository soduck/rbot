import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="join", description="ボイスチャンネルに参加します")
    async def join(self, interaction: discord.Interaction):
        print("/join が呼び出されました")
        if interaction.user.voice:
            channel = interaction.user.voice.channel
            try:
                if interaction.guild.voice_client is None:
                    await channel.connect()
                    await interaction.response.send_message("✅ ボイスチャンネルに参加しました！")
                else:
                    await interaction.guild.voice_client.move_to(channel)
                    await interaction.response.send_message("🔁 すでに接続済みなので移動しました！")
            except Exception as e:
                print(f"VC参加時のエラー: {e}")
                await interaction.response.send_message("❌ ボイスチャンネルに入れなかったよ。", ephemeral=True)
        else:
            await interaction.response.send_message("❗ 先にVCに入ってから使ってね！", ephemeral=True)

    @app_commands.command(name="leave", description="ボイスチャンネルから切断します")
    async def leave(self, interaction: discord.Interaction):
        print("/leave が呼び出されました")
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
            await interaction.response.send_message("👋 ボイスチャンネルから切断しました！")
        else:
            await interaction.response.send_message("❌ BotはまだVCにいないよ！", ephemeral=True)

    @app_commands.command(name="play", description="指定したURLの音楽を再生します")
    async def play(self, interaction: discord.Interaction, url: str):
        print("/play が呼び出されました")
        try:
            # BotがVCにいなければjoinする
            if interaction.guild.voice_client is None:
                if interaction.user.voice:
                    channel = interaction.user.voice.channel
                    await channel.connect()
                else:
                    await interaction.response.send_message("❗ 先にVCに入ってから使ってね！", ephemeral=True)
                    return

            # YouTubeから音声URLを取得
            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'noplaylist': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                stream_url = info['url']
                title = info.get("title", "Unknown Title")
                print(f"🎵 タイトル: {title}")
                print(f"🔗 ストリームURL: {stream_url}")

            # 音声ソースを生成して再生
            source = await discord.FFmpegOpusAudio.from_probe(stream_url)
            interaction.guild.voice_client.stop()
            interaction.guild.voice_client.play(source)
            await interaction.response.send_message(f"🎶 再生中: **{title}**")

        except Exception as e:
            print(f"再生エラー: {e}")
            await interaction.response.send_message("❌ 再生に失敗したよ。URLが正しいか、ログを見てね。", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Music(bot))
