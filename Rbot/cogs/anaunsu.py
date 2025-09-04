import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from discord.ui import View, Button
from asyncio import sleep

CONFIG_FILE = "announce_channels.json"
COOLDOWN_SECONDS = 60
ADMIN_ROLE_NAME = "監理者"  # 監理官ロール名をここで指定
DELETE_DELAY = 5  # メッセージ自動削除時間（秒）

class Announce(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channels = self.load_config()
        self.cooldowns = {}  # user_id: cooldown状態

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_config(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.channels, f, indent=4)

    @app_commands.command(name="setannounce", description="アナウンスチャンネルを設定します")
    @app_commands.checks.has_permissions(administrator=True)
    async def setannounce(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.channels[str(interaction.guild.id)] = channel.id
        self.save_config()
        await interaction.response.send_message(f"✅ {channel.mention} をアナウンスチャンネルに設定しました！", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # 監理官ロール確認
        if not any(role.name == ADMIN_ROLE_NAME for role in message.author.roles):
            return

        # クールダウン確認
        if message.author.id in self.cooldowns:
            await message.channel.send(f"⏳ クールダウン中です。もう少し待ってください。", delete_after=DELETE_DELAY)
            return

        # アナウンスチャンネル確認
        if str(message.guild.id) in self.channels:
            announce_channel_id = self.channels[str(message.guild.id)]
            if message.channel.id == announce_channel_id:
                content = message.content
                files = [await attachment.to_file() for attachment in message.attachments]
                sender = f"{message.author} ({message.guild.name})"

                # 確認メッセージを送信
                view = ConfirmView(message, content, files, sender, self.channels, self.bot, self.cooldowns)
                confirmation_msg = await message.channel.send("⚠️ 本当に送信しますか？", view=view)
                await sleep(DELETE_DELAY)
                await confirmation_msg.delete()

async def setup(bot):
    await bot.add_cog(Announce(bot))

class ConfirmView(View):
    def __init__(self, message, content, files, sender, channels, bot, cooldowns):
        super().__init__(timeout=30)
        self.message = message
        self.content = content
        self.files = files
        self.sender = sender
        self.channels = channels
        self.bot = bot
        self.cooldowns = cooldowns

    @discord.ui.button(label="はい", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.message.author:
            await interaction.response.send_message("❌ あなたはこの操作を行えません。", ephemeral=True)
            return

        # 他サーバーに転送
        for guild_id, channel_id in self.channels.items():
            if int(guild_id) != self.message.guild.id:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    embed = discord.Embed(
                        description=self.content if self.content else "（メッセージなし）",
                        color=discord.Color.green()
                    )
                    embed.set_author(name=self.sender, icon_url=self.message.author.display_avatar.url)
                    await channel.send(embed=embed, files=self.files if self.files else None)

        result_msg = await interaction.channel.send("✅ 送信しました！")
        await interaction.response.defer()
        await sleep(DELETE_DELAY)
        await result_msg.delete()

        self.cooldowns[self.message.author.id] = True
        await sleep(COOLDOWN_SECONDS)
        del self.cooldowns[self.message.author.id]

    @discord.ui.button(label="いいえ", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.message.author:
            await interaction.response.send_message("❌ あなたはこの操作を行えません。", ephemeral=True)
            return

        result_msg = await interaction.channel.send("❌ キャンセルしました。")
        await interaction.response.defer()
        await sleep(DELETE_DELAY)
        await result_msg.delete()
        self.stop()
