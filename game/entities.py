from game.generator import LaneType
from engine.ecs import PositionComponent, VelocityComponent, RenderComponent, ColliderComponent

def create_player(ecs_manager, assets, x, y, size):
    entity_id = ecs_manager.create_entity()
    
    graphics_item = assets.create_entity_graphic("chicken", size, size, "red")
    graphics_item.setZValue(2)
    
    ecs_manager.add_component(entity_id, PositionComponent(x, y))
    ecs_manager.add_component(entity_id, RenderComponent(graphics_item))
    ecs_manager.add_component(entity_id, ColliderComponent("player", size, size))
    
    return entity_id, graphics_item

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
    
    ecs_manager.add_component(entity_id, PositionComponent(x, y))
    ecs_manager.add_component(entity_id, RenderComponent(graphics_item))
    ecs_manager.add_component(entity_id, ColliderComponent(tag, size, size))
    
    return entity_id, graphics_item