import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import QTimer

from engine.world import WorldManager, WINDOW_WIDTH, WINDOW_HEIGHT, TILE_SIZE
from engine.physics import PhysicsEngine
from engine.ecs import EntityManager
from engine.events import EventManager, LoggerSystem 
from engine.view import GameView

from game.entities import create_player
from game.difficulty import DifficultyManager
from game.assets import AssetManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CrossyRoadGame")
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)

        self.assets = AssetManager(TILE_SIZE)
        self.ecs = EntityManager()
        self.event_manager = EventManager()
        self.logger = LoggerSystem(self.event_manager)
        self.physics = PhysicsEngine()
        self.difficulty = DifficultyManager() 
        
        self.world = WorldManager(self.ecs, self.difficulty, self.assets) 
        
        start_x = (WINDOW_WIDTH // TILE_SIZE // 2) * TILE_SIZE
        start_y = WINDOW_HEIGHT - (4 * TILE_SIZE)
        self.player_entity, player_rect = create_player(self.ecs, self.assets, start_x, start_y, TILE_SIZE)
        self.world.addItem(player_rect)

        self.view = GameView(self.world, self.player_entity, self.ecs, self.event_manager)
        self.setCentralWidget(self.view)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.game_loop)
        self.timer.start(int(1000 / 60))

    def game_loop(self):
        if self.physics.is_game_over:
            self.timer.stop()
            print(f"Twój wynik: {self.difficulty.current_score}")
            return

        self.difficulty.update(self.view.camera_y)
        self.view.update_camera(self.difficulty.camera_speed) 
        self.world.update_world(self.view.camera_y)
        self.physics.check_collisions(self.ecs, self.player_entity, self.world, self.view.camera_y, self.event_manager)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())