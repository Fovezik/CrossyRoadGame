from PyQt6.QtWidgets import QGraphicsRectItem, QGraphicsItemGroup, QGraphicsTextItem
from PyQt6.QtGui import QPen, QColor, QFont
from PyQt6.QtCore import Qt

from generator import LaneType
from ecs import PositionComponent, VelocityComponent, RenderComponent, ColliderComponent
from config import SETTINGS

def add_debug_rect(graphics_item, width, height):
    debug_rect = QGraphicsRectItem(0, 0, width, height)
    debug_rect.setPen(QPen(QColor("red"), 2, Qt.PenStyle.SolidLine))
    debug_rect.setZValue(10)
    debug_rect.setParentItem(graphics_item)
    debug_rect.setData(0, "debug_hitbox")
    debug_rect.setVisible(False)

def create_player(ecs_manager, assets, x, y, size):
    entity_id = ecs_manager.create_entity()
    
    size = SETTINGS.data["player_size"]
    graphics_item = assets.create_entity_graphic("chicken", size, size, "red")
    graphics_item.setZValue(2)
    add_debug_rect(graphics_item, size, size)
    
    ecs_manager.add_component(entity_id, PositionComponent(x, y))
    ecs_manager.add_component(entity_id, RenderComponent(graphics_item))
    ecs_manager.add_component(entity_id, ColliderComponent("player", size, size))
    
    return entity_id, graphics_item

def create_remote_player(ecs_manager, assets, x, y, size, player_id, name, color_name):
    entity_id = ecs_manager.create_entity()

    group = QGraphicsItemGroup()
    graphics_item = assets.create_entity_graphic("chicken", size, size, color_name)
    group.addToGroup(graphics_item)
    
    text_item = QGraphicsTextItem(name)
    text_item.setDefaultTextColor(QColor(color_name))
    text_item.setFont(QFont("Arial", 10, QFont.Weight.Bold))
    text_width = text_item.boundingRect().width()
    text_item.setPos((size - text_width) / 2, -20)
    group.addToGroup(text_item)
    
    group.setZValue(2.5)
    ecs_manager.add_component(entity_id, PositionComponent(x, y))
    ecs_manager.add_component(entity_id, RenderComponent(group))
    
    return entity_id, group

def create_obstacle(ecs_manager, assets, x, y, width, height, speed, direction, lane_type):
    entity_id = ecs_manager.create_entity()
    
    if lane_type == LaneType.ROAD:
        key = "truck" if width > height else "car"
        graphics_item = assets.create_entity_graphic(key, width, height, "yellow")
        tag = "car"
        
    elif lane_type == LaneType.RIVER:
        multiplier = int(width / height) 
        key = f"log_{multiplier}"
        graphics_item = assets.create_entity_graphic(key, width, height, "saddlebrown")
        tag = "log"
        
    graphics_item.setZValue(1)
    add_debug_rect(graphics_item, width, height)

    ecs_manager.add_component(entity_id, PositionComponent(x, y))
    ecs_manager.add_component(entity_id, VelocityComponent(speed * direction, 0.0))
    ecs_manager.add_component(entity_id, RenderComponent(graphics_item))
    ecs_manager.add_component(entity_id, ColliderComponent(tag, width, height))
    
    return entity_id, graphics_item

def create_static_obstacle(ecs_manager, assets, x, y, size, tag):
    entity_id = ecs_manager.create_entity()
    
    if tag == "tree":
        graphics_item = assets.create_entity_graphic("tree", size, size, "darkgreen")
        graphics_item.setZValue(1.5)
    elif tag == "lilypad":
        graphics_item = assets.create_entity_graphic("lilypad", size, size, "mediumseagreen")
        graphics_item.setZValue(0.5)
    
    add_debug_rect(graphics_item, size, size)

    ecs_manager.add_component(entity_id, PositionComponent(x, y))
    ecs_manager.add_component(entity_id, RenderComponent(graphics_item))
    ecs_manager.add_component(entity_id, ColliderComponent(tag, size, size))
    
    return entity_id, graphics_item