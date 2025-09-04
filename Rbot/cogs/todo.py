import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import re
from datetime import datetime, timedelta

DATA_FILE = "todo.json"

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def parse_time(time_str):
    pattern = r'(\d+)([smhd])'
    matches = re.findall(pattern, time_str)
    total_seconds = 0
    unit_map = {'s':1, 'm':60, 'h':3600, 'd':86400}
    for amount, unit in matches:
        total_seconds += int(amount) * unit_map[unit]
    return total_seconds

class Todo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()
        self.reminder_task.start()

    def cog_unload(self):
        self.reminder_task.cancel()

    @tasks.loop(seconds=10)
    async def reminder_task(self):
        now = datetime.utcnow().timestamp()
        for user_id, todos in list(self.data.items()):
            for todo in list(todos):
                if todo.get('deadline') and now >= todo['deadline']:
                    user = await self.bot.fetch_user(int(user_id))
                    embed = discord.Embed(title="⏰ TODO期限通知", description=f"<@{user_id}>\n「{todo['content']}」の期限です！")
                    view = TodoEndView(user_id, todo['content'], todo, self)
                    await user.send(embed=embed, view=view)
                    todos.remove(todo)
        save_data(self.data)

    @app_commands.command(name="todo_add", description="TODOを追加")
    @app_commands.describe(content="内容", time="時間 (例:1h30m)")
    async def todo_add(self, interaction: discord.Interaction, content: str, time: str = "0"):
        user_id = str(interaction.user.id)
        if user_id not in self.data:
            self.data[user_id] = []
        deadline = None
        if time != "0":
            seconds = parse_time(time)
            deadline = datetime.utcnow().timestamp() + seconds
        self.data[user_id].append({"content": content, "deadline": deadline})
        save_data(self.data)
        await interaction.response.send_message(f"✅ TODO「{content}」を追加しました。", ephemeral=True)

    @app_commands.command(name="todo_list", description="TODOリスト表示")
    async def todo_list(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        todos = self.data.get(user_id, [])
        if not todos:
            await interaction.response.send_message("TODOリストは空です。", ephemeral=True)
            return

        await interaction.response.send_message("✅ TODOリストを送信します（あなただけに表示）。", ephemeral=True)
        for idx, todo in enumerate(todos):
            content = todo['content']
            remaining = ""
            if todo['deadline']:
                delta = timedelta(seconds=int(todo['deadline'] - datetime.utcnow().timestamp()))
                remaining = f"（残り{delta}）"
            embed = discord.Embed(title=f"TODO {idx+1}", description=f"{content} {remaining}")
            view = SingleTodoView(user_id, idx, self)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="todo_request", description="他人にTODO依頼")
    @app_commands.describe(user="相手", content="内容", time="時間 (例:1d2h)")
    async def todo_request(self, interaction: discord.Interaction, user: discord.User, content: str, time: str = "0"):
        seconds = parse_time(time) if time != "0" else None
        deadline = datetime.utcnow().timestamp() + seconds if seconds else None
        view = TodoRequestView(user.id, content, deadline, self)
        await user.send(f"{interaction.user.name}さんから依頼が届きました！\n内容: {content}", view=view)
        await interaction.response.send_message(f"✅ {user.name}さんに依頼を送りました。", ephemeral=True)

class SingleTodoView(discord.ui.View):
    def __init__(self, user_id, todo_index, cog):
        super().__init__()
        self.user_id = user_id
        self.todo_index = todo_index
        self.cog = cog

    @discord.ui.button(label="完了", style=discord.ButtonStyle.green)
    async def complete(self, interaction: discord.Interaction, button: discord.ui.Button):
        todo = self.cog.data[self.user_id].pop(self.todo_index)
        save_data(self.cog.data)
        await interaction.response.send_message(f"✅ TODO「{todo['content']}」を完了しました。", ephemeral=True)

    @discord.ui.button(label="削除", style=discord.ButtonStyle.danger)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        todo = self.cog.data[self.user_id].pop(self.todo_index)
        save_data(self.cog.data)
        await interaction.response.send_message(f"🗑 TODO「{todo['content']}」を削除しました。", ephemeral=True)

    @discord.ui.button(label="改名", style=discord.ButtonStyle.primary)
    async def rename(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("新しいTODO内容を入力してください。", ephemeral=True)
        msg = await self.cog.bot.wait_for("message", check=lambda m: m.author == interaction.user and m.channel == interaction.channel)
        self.cog.data[self.user_id][self.todo_index]['content'] = msg.content
        save_data(self.cog.data)
        await interaction.followup.send(f"✏️ TODOを「{msg.content}」に改名しました。", ephemeral=True)

class TodoRequestView(discord.ui.View):
    def __init__(self, user_id, content, deadline, cog):
        super().__init__()
        self.user_id = str(user_id)
        self.content = content
        self.deadline = deadline
        self.cog = cog

    @discord.ui.button(label="引き受ける", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.user_id not in self.cog.data:
            self.cog.data[self.user_id] = []
        self.cog.data[self.user_id].append({"content": self.content, "deadline": self.deadline})
        save_data(self.cog.data)
        await interaction.response.send_message("✅ 引き受けました。TODOに追加しました。", ephemeral=True)

    @discord.ui.button(label="断る", style=discord.ButtonStyle.red)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🚫 依頼を断りました。", ephemeral=True)

class TodoEndView(discord.ui.View):
    def __init__(self, user_id, content, todo, cog):
        super().__init__()
        self.user_id = user_id
        self.content = content
        self.todo = todo
        self.cog = cog

    @discord.ui.button(label="延長する", style=discord.ButtonStyle.primary)
    async def extend(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("延長時間を入力してください（例: 1h, 30m）", ephemeral=True)
        msg = await self.cog.bot.wait_for("message", check=lambda m: m.author == interaction.user and m.channel == interaction.channel)
        seconds = parse_time(msg.content)
        self.todo['deadline'] = datetime.utcnow().timestamp() + seconds
        self.cog.data[str(interaction.user.id)].append(self.todo)
        save_data(self.cog.data)
        await interaction.followup.send(f"✅ 延長しました（残り: {msg.content}）。", ephemeral=True)

    @discord.ui.button(label="終了", style=discord.ButtonStyle.danger)
    async def end(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("✅ TODOを終了しました。", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Todo(bot))
