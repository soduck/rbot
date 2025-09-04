import json
import os

class StatsManager:
    def __init__(self, filepath="data/stats.json"):
        self.filepath = filepath
        self.data = self.load_stats()

    def load_stats(self):
        if not os.path.exists(self.filepath):
            return {}
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            # 壊れていたら初期化
            return {}

    def save_stats(self):
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def record_result(self, user_id, game_name, result):
        """
        user_id: strまたはint (DiscordのユーザーID)
        game_name: "janken" または "shiritori"
        result: "win" または "lose"
        """
        user_id = str(user_id)
        if user_id not in self.data:
            self.data[user_id] = {}
        if game_name not in self.data[user_id]:
            self.data[user_id][game_name] = {"win": 0, "lose": 0}
        if result in ["win", "lose"]:
            self.data[user_id][game_name][result] += 1
        self.save_stats()

    def get_stats(self, user_id, game_name):
        user_id = str(user_id)
        return self.data.get(user_id, {}).get(game_name, {"win": 0, "lose": 0})
