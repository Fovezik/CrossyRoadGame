import os
from PyQt6.QtGui import QPixmap, QBrush, QColor, QPen
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGraphicsRectItem, QGraphicsPixmapItem
from game.generator import LaneType

class AssetManager:
    def __init__(self, tile_size):
        self.tile_size = tile_size 
        self.lane_brushes = {}
        self.entity_pixmaps = {}
        
        self._load_lane_brushes()
        self._load_entity_pixmaps()

    def _load_lane_brushes(self):
        texture_paths = {
            "GRASS_DEFAULT": "assets/grass.png",
            "GRASS_AFTER_ROAD": "assets/grass_road.png",
            "GRASS_AFTER_RIVER": "assets/grass_river.png",
            LaneType.ROAD: "assets/road.png",
            LaneType.RIVER: "assets/river.png",
            LaneType.RIVER_LILY: "assets/river.png" 
        }
        fallback_colors = {
            "GRASS_DEFAULT": QColor("#54a800"),
            "GRASS_AFTER_ROAD": QColor("#4b9600"),
            "GRASS_AFTER_RIVER": QColor("#d2b48c"),
            LaneType.ROAD: QColor("#363636"),
            LaneType.RIVER: QColor("#00a2ff"),
            LaneType.RIVER_LILY: QColor("#00a2ff")
        }
        for key, path in texture_paths.items():
            if os.path.exists(path):
                pixmap = QPixmap(path)
                scaled_pixmap = pixmap.scaled(self.tile_size, self.tile_size, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.FastTransformation)
                self.lane_brushes[key] = QBrush(scaled_pixmap)
            else:
                self.lane_brushes[key] = QBrush(fallback_colors.get(key, QColor("black")))

    def _load_entity_pixmaps(self):
        """Ładuje grafiki postaci/przeszkód raz do pamięci RAM."""
        entity_paths = {
            "chicken": "assets/chicken.png",
            "car": "assets/car.png",
            "truck": "assets/truck.png",
            "log_2": "assets/log_2.png",
            "log_3": "assets/log_3.png",
            "log_4": "assets/log_4.png",
            "tree": "assets/tree.png",
            "lilypad": "assets/lilypad.png"
        }
        for key, path in entity_paths.items():
            if os.path.exists(path):
                self.entity_pixmaps[key] = QPixmap(path)

    def get_lane_brush(self, lane_key) -> QBrush:
        return self.lane_brushes.get(lane_key, QBrush(QColor("black")))

    def create_entity_graphic(self, entity_key: str, width: int, height: int, fallback_color: str):
        if entity_key in self.entity_pixmaps:
            pixmap = self.entity_pixmaps[entity_key]
            scaled_pixmap = pixmap.scaled(int(width), int(height), Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.FastTransformation)
            return QGraphicsPixmapItem(scaled_pixmap)
        else:
            rect = QGraphicsRectItem(0, 0, width, height)
            rect.setBrush(QBrush(QColor(fallback_color)))
            rect.setPen(QPen(Qt.PenStyle.NoPen))
            return rect