import json
import logging
from ecs import PositionComponent

class ReplayManager:
    def __init__(self):
        self.is_recording = False
        self.is_replaying = False
        self.seed = 0
        self.actions = []
        self.action_idx = 0

    def start_recording(self, seed):
        self.is_recording = True
        self.is_replaying = False
        self.seed = seed
        self.actions = []

    def record_action(self, frame, x, y):
        if self.is_recording:
            self.actions.append({"frame": frame, "x": x, "y": y})

    def start_replaying(self):
        self.is_recording = False
        self.is_replaying = True
        self.action_idx = 0
        return self.seed

    def apply_actions(self, frame, ecs, player_entity):
        if not self.is_replaying: 
            return
            
        pos = ecs.get_component(player_entity, PositionComponent)
        
        while self.action_idx < len(self.actions) and self.actions[self.action_idx]["frame"] == frame:
            action = self.actions[self.action_idx]
            if pos:
                pos.prev_x = pos.x
                pos.prev_y = pos.y
                pos.x = action["x"]
                pos.y = action["y"]
            self.action_idx += 1

    def save_to_file(self, filename="replay.json"):
        if not self.actions: return
        try:
            with open(filename, "w") as f:
                json.dump({"seed": self.seed, "actions": self.actions}, f)
            logging.info(f"Replay successfully saved to {filename}")
        except Exception as e:
            logging.error(f"Error saving replay: {e}")

    def load_from_file(self, filename="replay.json"):
        try:
            with open(filename, "r") as f:
                data = json.load(f)
                self.seed = data["seed"]
                self.actions = data["actions"]
                return self.start_replaying()
        except Exception as e:
            logging.error(f"Error loading replay: {e}")
            return None