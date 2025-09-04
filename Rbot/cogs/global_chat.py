import discord
from discord.ext import commands
import json
import os

CONFIG_FILE = "global_chat.json"

class GlobalChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.global_channels = self.load_config()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_config(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.global_channels, f, indent=4)

    def get_global_channel_ids(self):
        return list(self.global_channels.values())

    def get_global_channels(self):
        return [self.bot.get_channel(cid) for cid in self.global_channels.values()]

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setglobalchat(self, ctx, channel: discord.TextChannel):
        self.global_channels[str(ctx.guild.id)] = channel.id
        self.save_config()
        await ctx.send(f"✅ {channel.mention} をグローバルチャットに設定しました。")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return  # Botのメッセージは無視

        # 転送メッセージか確認（フッターで識別）
        if message.embeds:
            for embed in message.embeds:
                if embed.footer and embed.footer.text == "【GlobalChat転送】":
                    return  # 転送済みは無視

        if message.channel.id in self.get_global_channel_ids():
            sender = message.author
            origin_guild = message.guild.name if message.guild else "DM"
            origin_channel_id = message.channel.id

            files = []
            if message.attachments:
                for attachment in message.attachments:
                    fp = await attachment.to_file()
                    files.append(fp)

            for channel in self.get_global_channels():
                if channel and channel.id != origin_channel_id:
                    embed = discord.Embed(
                        description=message.content if message.content else None,
                        color=discord.Color.blue()
                    )
                    embed.set_author(name=f"{sender} ({origin_guild})", icon_url=sender.display_avatar.url)
                    embed.set_footer(text="【GlobalChat転送】")

                    if files:
                        await channel.send(embed=embed if message.content else None, files=files)
                    else:
                        await channel.send(embed=embed)

# setup関数を忘れずに
async def setup(bot):
    await bot.add_cog(GlobalChat(bot))
