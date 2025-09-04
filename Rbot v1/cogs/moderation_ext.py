import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import asyncio

WARN_LIMIT_KICK = 3
WARN_LIMIT_BAN = 5
CONFIG_FILE = "mod_channels.json"
WARN_FILE = "warns.json"
APPROVER_ROLE = "高等編集者"

class ModerationExt(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mod_channels = self.load_config(CONFIG_FILE)
        self.warns = self.load_config(WARN_FILE)
        self.pending_warns = {}

    def load_config(self, filename):
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_config(self, filename, data):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def get_mod_channel(self, guild):
        channel_id = self.mod_channels.get(str(guild.id))
        return self.bot.get_channel(channel_id) if channel_id else None

    @app_commands.command(name="setmodchannel", description="モデレーションチャンネルを設定します")
    @app_commands.checks.has_permissions(administrator=True)
    async def setmodchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.mod_channels[str(interaction.guild.id)] = channel.id
        self.save_config(CONFIG_FILE, self.mod_channels)
        await interaction.response.send_message(f"✅ モデレーション用チャンネルを {channel.mention} に設定しました。", ephemeral=True)

    @app_commands.command(name="warn", description="メンバーに警告を発行します（承認システム）")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        await self.start_pending_warn(interaction.guild, interaction.channel, interaction.user, member, reason)
        await interaction.response.send_message(f"⚠️ {member.mention} に警告リクエストを開始しました。", ephemeral=True)

    @app_commands.command(name="unwarn", description="メンバーの警告を取り消します")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def unwarn(self, interaction: discord.Interaction, member: discord.Member, index: int = -1):
        uid = str(member.id)
        if uid not in self.warns or not self.warns[uid]:
            await interaction.response.send_message(f"❌ {member.mention} に警告はありません。", ephemeral=True)
            return

        if index == -1:
            removed = self.warns[uid].pop()
        else:
            if index < 0 or index >= len(self.warns[uid]):
                await interaction.response.send_message("❌ 指定されたインデックスが無効です。", ephemeral=True)
                return
            removed = self.warns[uid].pop(index)

        self.save_config(WARN_FILE, self.warns)
        await interaction.response.send_message(f"✅ {member.mention} の警告を取り消しました（理由: {removed['reason']}）。", ephemeral=True)

    async def start_pending_warn(self, guild, channel, author, member, reason):
        mod_channel = self.get_mod_channel(guild) or channel
        msg = await mod_channel.send(
            f"⚠️ {author.mention} が {member.mention} に警告を発行しようとしています。\n理由: {reason}\n\n"
            f"🛡️ 承認ロール（{APPROVER_ROLE}）を持つ人は✅リアクションで承認してください（10分以内、2人必要）"
        )
        await msg.add_reaction("✅")
        self.pending_warns[msg.id] = {
            "member": member,
            "reason": reason,
            "author": author,
            "channel": channel,
            "mod_channel": mod_channel,
            "approvers": set()
        }

        await asyncio.sleep(600)
        if msg.id in self.pending_warns:
            await mod_channel.send(f"❌ {member.mention} の警告は承認されずキャンセルされました。")
            del self.pending_warns[msg.id]

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if reaction.message.id in self.pending_warns and str(reaction.emoji) == "✅":
            guild = reaction.message.guild
            role = discord.utils.get(guild.roles, name=APPROVER_ROLE)
            if role in user.roles:
                data = self.pending_warns[reaction.message.id]
                data['approvers'].add(user.id)

                if len(data['approvers']) >= 2:
                    await self.apply_warn(data)
                    del self.pending_warns[reaction.message.id]
            else:
                await reaction.message.channel.send(f"❌ {user.mention} は承認権限がありません。")

    async def apply_warn(self, data):
        member = data["member"]
        reason = data["reason"]
        ctx_channel = data["channel"]
        mod_channel = data["mod_channel"]
        author = data["author"]

        uid = str(member.id)
        if uid not in self.warns:
            self.warns[uid] = []
        self.warns[uid].append({"reason": reason, "by": author.name})
        self.save_config(WARN_FILE, self.warns)
        warn_count = len(self.warns[uid])

        await ctx_channel.send(f"⚠️ {member.mention} に警告を与えました（合計 {warn_count} 回）")
        await mod_channel.send(f"✅ 承認者が2人に達したため警告を実行しました。")

        if warn_count == WARN_LIMIT_KICK:
            try:
                await member.kick(reason="警告数上限に達したため")
                await mod_channel.send(f"🚨 {member.mention} をKickしました（警告数: {warn_count}）")
            except:
                await mod_channel.send("❌ Kickできません（権限不足）")
        elif warn_count == WARN_LIMIT_BAN:
            try:
                await member.ban(reason="警告数上限に達したため")
                await mod_channel.send(f"🚨 {member.mention} をBanしました（警告数: {warn_count}）")
            except:
                await mod_channel.send("❌ Banできません（権限不足）")

    @app_commands.command(name="report", description="メンバーを通報します")
    async def report(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        try:
            await interaction.user.send(f"✅ {member.display_name} を通報しました（理由: {reason}）。")
        except:
            pass

        mod_channel = self.get_mod_channel(interaction.guild)
        if not mod_channel:
            await interaction.response.send_message("❌ モデレーションチャンネルが設定されていません。/setmodchannel で設定してください。", ephemeral=True)
            return

        view = ReportView(member, reason, interaction.user, self, mod_channel)
        msg = await mod_channel.send(
            f"🚨 **通報がありました！**\n"
            f"通報者: {interaction.user.mention}\n"
            f"対象: {member.mention}\n"
            f"理由: {reason}",
            view=view
        )
        view.set_message(msg)
        await interaction.response.send_message("✅ 通報を送信しました。", ephemeral=True)

class ReportView(discord.ui.View):
    def __init__(self, member, reason, reporter, cog, mod_channel):
        super().__init__(timeout=None)
        self.button = self.WarnButton(member, reason, reporter, cog, mod_channel)
        self.add_item(self.button)
        self.message = None

    def set_message(self, message):
        self.message = message
        self.button.set_message(message)

    class WarnButton(discord.ui.Button):
        def __init__(self, member, reason, reporter, cog, mod_channel):
            super().__init__(style=discord.ButtonStyle.danger, label="⚠️ 審査リクエスト")
            self.member = member
            self.reason = reason
            self.reporter = reporter
            self.cog = cog
            self.mod_channel = mod_channel
            self.message = None

        def set_message(self, message):
            self.message = message

        async def callback(self, interaction: discord.Interaction):
            if self.message:
                try:
                    await self.message.delete()
                except:
                    pass
            await interaction.response.send_message(f"🛡️ {interaction.user.mention} によって警告審査が開始されました。", ephemeral=True)
            await self.cog.start_pending_warn(
                interaction.guild, interaction.channel, self.reporter, self.member, self.reason
            )

async def setup(bot):
    await bot.add_cog(ModerationExt(bot))
