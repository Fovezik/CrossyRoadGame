from dataclasses import dataclass
from typing import Type, TypeVar, Any

T = TypeVar('T')

@dataclass
class PositionComponent:
    x: float
    y: float
    prev_x: float = 0.0
    prev_y: float = 0.0

@dataclass
class VelocityComponent:
    vx: float
    vy: float

@dataclass
class RenderComponent:
    graphics_item: Any 

@dataclass
class ColliderComponent:
    tag: str
    width: float
    height: float
    
@dataclass
class AIComponent:
    state: str = "IDLE"
    timer: int = 0


class EntityManager:
    def __init__(self):
        self.next_entity_id = 0
        self.entities = {}

    def create_entity(self) -> int:
        entity_id = self.next_entity_id
        self.entities[entity_id] = {}
        self.next_entity_id += 1
        return entity_id

    def destroy_entity(self, entity_id: int):
        if entity_id in self.entities:
            del self.entities[entity_id]

    def add_component(self, entity_id: int, component: Any):
        comp_type = type(component)
        self.entities[entity_id][comp_type] = component

    def get_component(self, entity_id: int, comp_type: Type[T]) -> T:
        return self.entities[entity_id].get(comp_type)

    def has_component(self, entity_id: int, comp_type: Type[T]) -> bool:
        return comp_type in self.entities[entity_id]

    def get_entities_with(self, *component_types: Type) -> list[int]:
        matching_entities = []
        for entity_id, components in self.entities.items():
            if all(comp_type in components for comp_type in component_types):
                matching_entities.append(entity_id)
        return matching_entities
    
    def clear_all(self):
        self.entities.clear()
        self.next_entity_id = 0


class MovementSystem:
    def update(self, manager: EntityManager):
        for entity in manager.get_entities_with(PositionComponent, VelocityComponent):
            pos = manager.get_component(entity, PositionComponent)
            vel = manager.get_component(entity, VelocityComponent)
            pos.x += vel.vx
            pos.y += vel.vy

class RenderSystem:
    def update(self, manager: EntityManager):
        for entity in manager.get_entities_with(PositionComponent, RenderComponent):
            pos = manager.get_component(entity, PositionComponent)
            render = manager.get_component(entity, RenderComponent)
            render.graphics_item.setPos(pos.x, pos.y)