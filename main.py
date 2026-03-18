import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QGraphicsRectItem
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QBrush, QColor, QPen

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 1200
TILE_SIZE = 40
FPS = 60

class GameScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setBackgroundBrush(QBrush(QColor("darkgray")))
        self.player = QGraphicsRectItem(0, 0, TILE_SIZE, TILE_SIZE)
        self.player.setBrush(QBrush(QColor("red")))
        self.player.setPen(QPen(Qt.PenStyle.NoPen))
        start_x = (WINDOW_WIDTH // TILE_SIZE // 2) * TILE_SIZE
        start_y = WINDOW_HEIGHT - (2 * TILE_SIZE)
        self.player.setPos(start_x, start_y)
        self.addItem(self.player)

    def update_game(self):
        pass

class GameView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.BoundingRectViewportUpdate)
        self.game_scene = scene

    def keyPressEvent(self, event):
        player = self.game_scene.player
        current_x = player.x()
        current_y = player.y()
        if event.key() == Qt.Key.Key_W or event.key() == Qt.Key.Key_Up: 
            player.setPos(current_x, current_y - TILE_SIZE)
        elif event.key() == Qt.Key.Key_S or event.key() == Qt.Key.Key_Down: 
            player.setPos(current_x, current_y + TILE_SIZE)
        elif event.key() == Qt.Key.Key_A or event.key() == Qt.Key.Key_Left: 
            player.setPos(current_x - TILE_SIZE, current_y)
        elif event.key() == Qt.Key.Key_D or event.key() == Qt.Key.Key_Right: 
            player.setPos(current_x + TILE_SIZE, current_y)
        else:
            super().keyPressEvent(event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Crossy Road Engine - PyQt")
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.scene = GameScene()
        self.view = GameView(self.scene)
        self.setCentralWidget(self.view)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.scene.update_game)
        self.timer.start(int(1000 / FPS))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())