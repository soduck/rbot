import discord
from discord.ext import commands
from discord import app_commands
import json
import random
import os
from datetime import datetime, timedelta

ECONOMY_FILE = "economy.json"
SHOP_FILE = "shop_roles.json"
COOLDOWN_FILE = "work_cooldown.json"

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        for file in [ECONOMY_FILE, SHOP_FILE, COOLDOWN_FILE]:
            if not os.path.exists(file):
                with open(file, "w") as f:
                    json.dump({} if file != SHOP_FILE else {"VIP": 100, "King": 500}, f)

    def get_balance(self, user_id):
        with open(ECONOMY_FILE, "r") as f:
            data = json.load(f)
        return data.get(str(user_id), 0)

    def update_balance(self, user_id, amount):
        with open(ECONOMY_FILE, "r") as f:
            data = json.load(f)
        data[str(user_id)] = data.get(str(user_id), 0) + amount
        with open(ECONOMY_FILE, "w") as f:
            json.dump(data, f)

    def get_cooldown(self, user_id):
        with open(COOLDOWN_FILE, "r") as f:
            cooldowns = json.load(f)
        return cooldowns.get(str(user_id))

    def set_cooldown(self, user_id):
        with open(COOLDOWN_FILE, "r") as f:
            cooldowns = json.load(f)
        cooldowns[str(user_id)] = datetime.now().isoformat()
        with open(COOLDOWN_FILE, "w") as f:
            json.dump(cooldowns, f)

    @app_commands.command(name="balance", description="自分の所持金を確認します")
    async def balance(self, interaction: discord.Interaction):
        bal = self.get_balance(interaction.user.id)
        await interaction.response.send_message(f"💰 {interaction.user.mention} の所持金：{bal}コイン")

    @app_commands.command(name="work", description="働いてコインを稼ぎます（1日1回）")
    async def work(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        last_work_time = self.get_cooldown(user_id)

        if last_work_time:
            last_time = datetime.fromisoformat(last_work_time)
            now = datetime.now()
            if now - last_time < timedelta(days=1):
                remaining = timedelta(days=1) - (now - last_time)
                hours, remainder = divmod(remaining.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                await interaction.response.send_message(
                    f"❌ 次の `/work` はあと {hours}時間{minutes}分{seconds}秒 後に実行できます。",
                    ephemeral=True
                )
                return

        earnings = random.randint(50, 150)
        self.update_balance(user_id, earnings)
        self.set_cooldown(user_id)
        await interaction.response.send_message(f"💼 {interaction.user.mention} が働いて {earnings}コイン稼ぎました！")

    @app_commands.command(name="pay", description="他のユーザーにコインを送金します")
    async def pay(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        if amount <= 0:
            await interaction.response.send_message("❌ 送金額は正の数を入力してください。", ephemeral=True)
            return
        if self.get_balance(interaction.user.id) < amount:
            await interaction.response.send_message("❌ 残高不足です。", ephemeral=True)
            return
        self.update_balance(interaction.user.id, -amount)
        self.update_balance(member.id, amount)
        await interaction.response.send_message(f"💸 {interaction.user.mention} から {member.mention} に {amount}コイン送金しました！")

    @app_commands.command(name="shop", description="ロールショップを表示します")
    async def shop(self, interaction: discord.Interaction):
        with open(SHOP_FILE, "r") as f:
            shop_data = json.load(f)
        msg = "🛒 **ロールショップ**\n"
        for role, price in shop_data.items():
            msg += f"- {role}: {price}コイン\n"
        await interaction.response.send_message(msg)

    @app_commands.command(name="buy", description="ロールを購入します")
    async def buy(self, interaction: discord.Interaction, role_name: str):
        with open(SHOP_FILE, "r") as f:
            shop_data = json.load(f)
        role = discord.utils.get(interaction.guild.roles, name=role_name)
        if role_name not in shop_data or role is None:
            await interaction.response.send_message("❌ そのロールは販売されていません。", ephemeral=True)
            return
        price = shop_data[role_name]
        if self.get_balance(interaction.user.id) < price:
            await interaction.response.send_message("❌ 残高不足です。", ephemeral=True)
            return
        self.update_balance(interaction.user.id, -price)
        await interaction.user.add_roles(role)
        await interaction.response.send_message(f"✅ {role_name} を購入し、付与しました！")

    @app_commands.command(name="casino", description="カジノに挑戦します")
    async def casino(self, interaction: discord.Interaction, amount: int):
        if amount <= 0:
            await interaction.response.send_message("❌ 掛け金は正の数を入力してください。", ephemeral=True)
            return
        if self.get_balance(interaction.user.id) < amount:
            await interaction.response.send_message("❌ 残高不足です。", ephemeral=True)
            return
        result = random.choices(["当たり", "はずれ"], weights=[30, 70])[0]
        if result == "当たり":
            winnings = amount * 2
            self.update_balance(interaction.user.id, amount)
            await interaction.response.send_message(f"🎰 大当たり！ {amount}コインが{winnings}コインになりました！")
        else:
            self.update_balance(interaction.user.id, -amount)
            await interaction.response.send_message(f"🎰 残念… {amount}コイン失いました。")

async def setup(bot):
    await bot.add_cog(Economy(bot))
