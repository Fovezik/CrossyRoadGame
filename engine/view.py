from PyQt6.QtWidgets import QGraphicsView
from PyQt6.QtCore import Qt
from engine.ecs import PositionComponent
from engine.world import WINDOW_WIDTH, WINDOW_HEIGHT, TILE_SIZE

class GameView(QGraphicsView):
    def __init__(self, world_scene, player_entity_id, ecs_manager, event_manager, parent=None):
        super().__init__(world_scene, parent)
        self.player_entity = player_entity_id
        self.ecs = ecs_manager
        self.events = event_manager
        
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        initial_pos = self.ecs.get_component(self.player_entity, PositionComponent)
        self.camera_y = initial_pos.y - 100 
        
        self.centerOn(WINDOW_WIDTH / 2, self.camera_y)

    def update_camera(self, current_camera_speed):
        """Kamera aktualizuje się z prędkością podaną przez system trudności."""
        self.camera_y -= current_camera_speed
        
        pos = self.ecs.get_component(self.player_entity, PositionComponent)
        if not pos: return

        distance_to_center = self.camera_y - pos.y
        max_distance = (WINDOW_HEIGHT / 2) - (3 * TILE_SIZE)

        if distance_to_center > max_distance:
            self.camera_y = pos.y + max_distance

        self.centerOn(WINDOW_WIDTH / 2, self.camera_y)

    def keyPressEvent(self, event):
        if not event: return
        
        pos = self.ecs.get_component(self.player_entity, PositionComponent)
        if not pos: return

        pos.prev_x = pos.x
        pos.prev_y = pos.y

        direction = None 
        snapped_x = round(pos.x / TILE_SIZE) * TILE_SIZE

        if event.key() == Qt.Key.Key_Up or event.key() == Qt.Key.Key_W:
            pos.y -= TILE_SIZE
            pos.x = snapped_x
            direction = "GÓRA"
        elif event.key() == Qt.Key.Key_Down or event.key() == Qt.Key.Key_S:
            pos.y += TILE_SIZE
            pos.x = snapped_x
            direction = "DÓŁ"
        elif event.key() == Qt.Key.Key_Left or event.key() == Qt.Key.Key_A:
            if snapped_x - TILE_SIZE >= 0:
                pos.x = snapped_x - TILE_SIZE
                direction = "LEWO"
        elif event.key() == Qt.Key.Key_Right or event.key() == Qt.Key.Key_D:
            if snapped_x + TILE_SIZE < WINDOW_WIDTH:
                pos.x = snapped_x + TILE_SIZE
                direction = "PRAWO"
        else:
            super().keyPressEvent(event)
            
        if direction:
            self.events.emit("PLAYER_MOVED", direction=direction, new_x=pos.x, new_y=pos.y)