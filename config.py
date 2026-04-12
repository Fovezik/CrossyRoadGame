import json
import os
import logging

TILE_SIZE = 40
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 800

class GameConfig:
    def __init__(self):
        self.data = {}
        self.load()

    def load(self):
        if os.path.exists("config.json"):
            try:
                with open("config.json", "r") as f:
                    self.data = json.load(f)
            except Exception as e:
                logging.error(f"Error loading config.json: {e}")

        self.data["player_size"] = self.data.get("player_size", 40)
        self.data["camera_start_speed"] = self.data.get("camera_start_speed", 0.5)
        self.data["camera_max_speed"] = self.data.get("camera_max_speed", 3.5)
        self.data["camera_accel"] = self.data.get("camera_accel", 0.0001)
        self.data["camera_chase"] = self.data.get("camera_chase", False)
        self.data["obstacle_speed"] = self.data.get("obstacle_speed", 1.0)
        self.data["spawn_rate"] = self.data.get("spawn_rate", 1.0)
        if not isinstance(self.data.get("custom_map"), list):
            self.data["custom_map"] = ["Grass", "Grass", "Grass", "Grass", "Grass", "Grass", "Grass", "Grass", "Grass"]
        self.data["high_score"] = self.data.get("high_score", 0)

    def write_high_score(self, score):
        self.data["high_score"] = score
        try:
            with open("config.json", "w") as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            logging.error(f"Error writing high score to config.json: {e}")

SETTINGS = GameConfig()