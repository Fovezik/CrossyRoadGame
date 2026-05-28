import sys
import json
import random
import socket
import threading
import queue
import json
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QWidget, QVBoxLayout
from PyQt6.QtCore import QTimer, Qt

from config import TILE_SIZE, WINDOW_WIDTH, WINDOW_HEIGHT, SETTINGS
from generator import LaneType
from world import WorldManager
from physics import PhysicsEngine
from ecs import EntityManager, PositionComponent
from events import EventManager, LoggerSystem 
from view import GameView
from entities import create_player, create_remote_player, create_ai_enemy
from difficulty import DifficultyManager
from assets import AssetManager
from replay import ReplayManager
from ai import AISystem

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CrossyRoadGame")
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        
        self.frame_count = 0 
        self.replay = ReplayManager()

        self.my_id = None
        self.remote_players = {}
        self.net_queue = queue.Queue()
        self.client = None
        self.is_multiplayer = False
        self.ai_mode = False
        
        self.assets = AssetManager(TILE_SIZE)
        self.ecs = EntityManager()
        self.event_manager = EventManager()
        self.logger = LoggerSystem(self.event_manager)
        self.physics = PhysicsEngine()
        self.ai_system = AISystem()
        self.difficulty = DifficultyManager() 
        self.world = WorldManager(self.ecs, self.difficulty, self.assets) 
        
        self.view = GameView(self.world, None, self.ecs, self.event_manager)
        self.setCentralWidget(self.view)
        
        self.event_manager.subscribe("TogglePauseEvent", lambda e: self.toggle_pause())
        self.event_manager.subscribe("GameOverEvent", lambda e: self.game_over())
        self.event_manager.subscribe("PlayerMovedEvent", self.on_player_moved)
        self.event_manager.subscribe("ReloadConfigEvent", lambda e: self.hot_reload())

        self.high_score = SETTINGS.data["high_score"]

        self.game_state = "MENU"
        self.setup_ui()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.game_loop)
        
        self.net_timer = QTimer(self)
        self.net_timer.timeout.connect(self.process_net_queue)
        self.net_timer.start(16)
        
        self.current_seed = 1234
        #self.current_seed = random.randint(0, 999999)
        self.start(self.current_seed, is_replay=False, lock_input=True)

    def listen_to_server(self):
        buffer = ""
        while True:
            try:
                data = self.client.recv(1024).decode('utf8')
                if not data: break
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    msg = json.loads(line)
                    self.net_queue.put(msg)
            except:
                break

    def setup_ui(self):
        self.score_label = QLabel(f"Score: 0\nHigh Score: {self.high_score}", self.view)
        self.score_label.setStyleSheet("color: white; font-size: 15px; font-weight: bold; background-color: rgba(0, 0, 0, 150); padding: 5px; border-radius: 5px;")
        self.score_label.setGeometry(WINDOW_WIDTH - 160, 10, 150, 50)
        self.score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.score_label.hide()

        self.menu_overlay = QWidget(self.view)
        self.menu_overlay.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.menu_overlay.setStyleSheet("background-color: rgba(0, 0, 0, 180);")
        
        layout = QVBoxLayout(self.menu_overlay)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.title_label = QLabel("CROSSY ROAD", self.menu_overlay)
        self.title_label.setStyleSheet("color: white; font-size: 50px; font-weight: bold; background: transparent;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignCenter)

        def create_btn(text, color, callback):
            btn = QPushButton(text, self.menu_overlay)
            btn.setFixedSize(250, 60)
            btn.setStyleSheet(f"QPushButton {{ font-size: 20px; font-weight: bold; color: white; background-color: {color}; border-radius: 10px; margin-top: 10px; }} QPushButton:hover {{ opacity: 0.8; }}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(callback)
            layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
            return btn

        self.action_btn = create_btn("LOCAL PLAY", "#4CAF50", self.handle_action_btn)
        self.ai_btn = create_btn("AI MODE: OFF", "#607D8B", self.toggle_ai_mode)
        self.connect_btn = create_btn("CONNECT TO SERVER", "#E91E63", self.handle_connect_btn)
        self.start_multi_btn = create_btn("START MULTIPLAYER", "#E91E63", self.handle_start_multi)
        self.load_replay_btn = create_btn("LOAD REPLAY", "#9C27B0", self.load_replay)
        self.replay_btn = create_btn("WATCH REPLAY", "#2196F3", self.watch_replay)
        self.save_replay_btn = create_btn("SAVE REPLAY", "#FF9800", self.save_replay)

        self.start_multi_btn.hide()
        self.replay_btn.hide()
        self.save_replay_btn.hide()

    def start(self, seed, is_replay=False, lock_input=False, ai_mode=False):
        random.seed(seed)
        self.current_seed = seed
        self.frame_count = 0
        
        if not is_replay:
            self.replay.start_recording(seed)

        self.ecs.clear_all()
        self.difficulty.reset()
        
        self.world.is_host = not self.is_multiplayer or getattr(self, 'my_id', None) == 1
        self.world.on_spawn_obstacle = self.on_spawn_obstacle
        self.world.reset(seed)

        start_x = (WINDOW_WIDTH // TILE_SIZE // 2) * TILE_SIZE
        start_y = WINDOW_HEIGHT - (4 * TILE_SIZE)
        
        if ai_mode:
            self.player_entity, player_rect = create_ai_enemy(self.ecs, self.assets, start_x, start_y, TILE_SIZE)
        else:
            self.player_entity, player_rect = create_player(self.ecs, self.assets, start_x, start_y, TILE_SIZE)
            
        self.world.addItem(player_rect)
        self.view.player_entity = self.player_entity
        self.view.camera_y = start_y - 100
        self.view.centerOn(WINDOW_WIDTH / 2, self.view.camera_y)

        self.score_label.setText(f"Score: 0\nHigh Score: {self.high_score}")
        self.view.input_locked = lock_input
        
        if not lock_input or is_replay:
            self.game_state = "PLAYING"
            self.menu_overlay.hide()
            self.score_label.show()
            self.timer.start(int(1000 / 60))
            self.view.setFocus()

    def toggle_ai_mode(self):
        self.ai_mode = not self.ai_mode
        self.ai_btn.setText(f"AI MODE: {'ON' if self.ai_mode else 'OFF'}")

    def handle_connect_btn(self):
        if self.game_state in ["MENU", "GAME_OVER"]:
            try:
                self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client.connect((SETTINGS.data["host"], SETTINGS.data["port"]))
                threading.Thread(target=self.listen_to_server, daemon=True).start()
                self.is_multiplayer = True
                self.ai_mode = False
            except Exception as e:
                print(f"Connection failed: {e}")
                return
                
            self.title_label.setText("WAITING FOR PLAYERS...")
            self.action_btn.hide()
            self.ai_btn.hide()
            self.connect_btn.hide()
            self.load_replay_btn.hide()
            self.replay_btn.hide()
            self.save_replay_btn.hide()

    def handle_start_multi(self):
        seed = random.randint(0, 999999)
        msg = {"type": "START", "seed": seed}
        try:
            self.client.send((json.dumps(msg) + "\n").encode('utf8'))
        except Exception as e:
            pass
        self.start(seed, is_replay=False, lock_input=False, ai_mode=False)

    def handle_action_btn(self):
        if self.game_state == "MENU":
            self.is_multiplayer = False
            self.start(self.current_seed, is_replay=False, lock_input=False, ai_mode=self.ai_mode)
        elif self.game_state == "PAUSED":
            self.game_state = "PLAYING"
            self.menu_overlay.hide()
            self.score_label.show()
            self.view.input_locked = False
            self.timer.start(int(1000 / 60))
            self.view.setFocus()
        elif self.game_state == "GAME_OVER":
            self.is_multiplayer = False
            self.start(self.current_seed, is_replay=False, lock_input=False, ai_mode=self.ai_mode)
            self.replay_btn.hide()
            self.save_replay_btn.hide()

    def toggle_pause(self):
        if self.game_state in ["MENU", "GAME_OVER"]: return

        if self.game_state == "PLAYING":
            self.game_state = "PAUSED"
            self.timer.stop()
            self.view.input_locked = True
            
            self.title_label.setText("PAUSED")
            self.action_btn.setText("RESUME")
            self.action_btn.setStyleSheet("font-size: 24px; font-weight: bold; color: white; background-color: #4CAF50; border-radius: 10px;")
            self.ai_btn.hide()
            self.connect_btn.hide()
            self.menu_overlay.show()
            
        elif self.game_state == "PAUSED":
            self.handle_action_btn()

    def game_over(self):
        if self.game_state == "GAME_OVER": return 
        
        self.game_state = "GAME_OVER"
        self.timer.stop()
        self.view.input_locked = True
        
        if self.difficulty.current_score > self.high_score:
            self.high_score = self.difficulty.current_score
            SETTINGS.write_high_score(self.high_score)

        self.title_label.setText(f"GAME OVER\nScore: {self.difficulty.current_score}\nHigh Score: {self.high_score}\n")
        self.title_label.setStyleSheet("color: #F44336; font-size: 40px; font-weight: bold; background: transparent;")
        
        self.action_btn.setText("PLAY AGAIN")
        self.action_btn.setStyleSheet("font-size: 24px; font-weight: bold; color: white; background-color: #F44336; border-radius: 10px;")
        self.action_btn.show()

        self.save_replay_btn.setText("SAVE REPLAY")
        self.save_replay_btn.setStyleSheet("font-size: 20px; font-weight: bold; color: white; background-color: #FF9800; border-radius: 10px; margin-top: 10px;")
        self.save_replay_btn.show()
        
        self.ai_btn.show()
        self.connect_btn.show()
        self.replay_btn.show()
        self.load_replay_btn.hide()
        
        self.menu_overlay.show()

    def process_net_queue(self):
        while not self.net_queue.empty():
            msg = self.net_queue.get()
            
            if msg["type"] == "INIT": 
                self.my_id = msg["id"]
                if self.is_multiplayer and self.game_state in ["MENU", "GAME_OVER"]:
                    if self.my_id == 1:
                        self.title_label.setText("YOU ARE HOST")
                        self.start_multi_btn.show()
                    else:
                        self.title_label.setText("WAITING FOR HOST TO START...")
                        
            elif msg["type"] == "START":
                self.start(msg["seed"], is_replay=False, lock_input=False, ai_mode=False)

            elif msg["type"] == "SPAWN_OBSTACLE":
                self.world.spawn_obstacle_from_net(
                    msg["x"], msg["y"], msg["width"], 
                    msg["speed"], msg["direction"], LaneType(msg["lane_type"])
                )

            elif msg["type"] == "MOVE":
                pid = msg["id"]
                if pid not in self.remote_players:
                    size = SETTINGS.data.get("player_size", 40)
                    ecs_id, rect = create_remote_player(
                        self.ecs, self.assets, msg["x"], msg["y"], size, 
                        pid, f"Gracz {pid}", "blue"
                    )
                    self.world.addItem(rect)
                    self.remote_players[pid] = ecs_id
                
                else:
                    ecs_id = self.remote_players[pid]
                    pos = self.ecs.get_component(ecs_id, PositionComponent)
                    if pos:
                        pos.x = msg["x"]
                        pos.y = msg["y"]
                        
    def game_loop(self):
        self.frame_count += 1
        if self.replay.is_replaying:
            self.replay.apply_actions(self.frame_count, self.ecs, self.player_entity)
            
        self.ai_system.update(self.ecs, self.world)
        self.difficulty.update(self.view.camera_y)
        self.view.update_camera(self.difficulty.camera_speed) 
        self.world.update_world(self.view.camera_y)
        self.physics.check_collisions(self.ecs, self.player_entity, self.world, self.view.camera_y, self.event_manager)
        self.score_label.setText(f"Score: {self.difficulty.current_score}\nHigh Score: {self.high_score}")

    def on_player_moved(self, event):
        self.replay.record_action(self.frame_count, event.x, event.y)
        if getattr(self, 'is_multiplayer', False) and self.my_id is not None and getattr(self, 'client', None):
            msg = {"type": "MOVE", "id": self.my_id, "x": event.x, "y": event.y}
            try:
                self.client.send((json.dumps(msg) + "\n").encode('utf8'))
            except Exception as e:
                print(f"Network error: {e}")

    def on_spawn_obstacle(self, x, y, width, speed, direction, lane_type):
        if getattr(self, 'is_multiplayer', False) and getattr(self, 'my_id', None) == 1 and getattr(self, 'client', None):
            msg = {
                "type": "SPAWN_OBSTACLE",
                "x": x, "y": y, "width": width,
                "speed": speed, "direction": direction,
                "lane_type": lane_type.value
            }
            try:
                self.client.send((json.dumps(msg) + "\n").encode('utf8'))
            except Exception as e:
                pass
    
    def watch_replay(self):
        saved_seed = self.replay.start_replaying()
        self.start(saved_seed, is_replay=True, lock_input=True)

    def save_replay(self):
        self.replay.save_to_file("replay.json")
        self.save_replay_btn.setText("SAVED!")
        self.save_replay_btn.setStyleSheet("font-size: 20px; font-weight: bold; color: white; background-color: #9E9E9E; border-radius: 10px; margin-top: 10px;")

    def load_replay(self):
        saved_seed = self.replay.load_from_file("replay.json")
        if saved_seed is not None:
            self.start(saved_seed, is_replay=True, lock_input=True)

    def hot_reload(self):
        SETTINGS.load()
        #self.current_seed = random.randint(0, 999999)
        self.start(self.current_seed, is_replay=False, lock_input=False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())