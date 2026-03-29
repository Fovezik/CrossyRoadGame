import random
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsRectItem
from PyQt6.QtGui import QPen
from PyQt6.QtCore import Qt

from config import TILE_SIZE, WINDOW_WIDTH, WINDOW_HEIGHT
from generator import MapGenerator, LaneType
from entities import create_obstacle, create_static_obstacle
from ecs import MovementSystem, RenderSystem, PositionComponent, VelocityComponent, RenderComponent

class WorldManager(QGraphicsScene):
    def __init__(self, ecs_manager, difficulty_manager, asset_manager, parent=None):
        super().__init__(parent)
        self.ecs = ecs_manager
        self.difficulty = difficulty_manager
        self.assets = asset_manager
        self.generator = MapGenerator()
        
        self.active_lanes_info = [] 
        self.obstacles = []
        self.highest_y = WINDOW_HEIGHT 

        self.movement_system = MovementSystem()
        self.render_system = RenderSystem()

        self.debug_mode = False

        for _ in range((WINDOW_HEIGHT // TILE_SIZE) + 2):
            self.spawn_new_lane_row()

    def toggle_debug_mode(self):
        self.debug_mode = not self.debug_mode
        for item in self.items():
            if item.data(0) == "debug_hitbox":
                item.setVisible(self.debug_mode)
                
    def apply_debug_to_new_item(self, graphics_item):
        for child in graphics_item.childItems():
            if child.data(0) == "debug_hitbox":
                child.setVisible(self.debug_mode)

    def spawn_new_lane_row(self):
        self.highest_y -= TILE_SIZE 
        if len(self.active_lanes_info) < 5:
            lane_data = self.generator.generate_initial_map(1)[0]
        else:
            lane_data = self.generator.generate_next_lane()
            
        lane_data = self.difficulty.apply_to_lane_data(lane_data) 
        
        lane_item = QGraphicsRectItem(0, self.highest_y, WINDOW_WIDTH, TILE_SIZE)
        
        brush_key = None
        if lane_data.lane_type == LaneType.GRASS:
            prev_lane_type = self.active_lanes_info[-1][0].lane_type if self.active_lanes_info else None
                
            if prev_lane_type == LaneType.ROAD:
                brush_key = "GRASS_AFTER_ROAD"
            elif prev_lane_type in (LaneType.RIVER, LaneType.RIVER_LILY):
                brush_key = "GRASS_AFTER_RIVER"
            else:
                brush_key = "GRASS_DEFAULT"
                
        elif lane_data.lane_type == LaneType.RIVER_LILY:
            brush_key = LaneType.RIVER
        else:
            brush_key = lane_data.lane_type
            
        lane_item.setBrush(self.assets.get_lane_brush(brush_key))
        lane_item.setPen(QPen(Qt.PenStyle.NoPen))
        lane_item.setZValue(0) 
        
        self.addItem(lane_item)
        self.active_lanes_info.append([lane_data, self.highest_y, lane_item, 0])

        if lane_data.lane_type == LaneType.GRASS:
            for _ in range(random.randint(0, 3)):
                x = random.randint(0, (WINDOW_WIDTH // TILE_SIZE) - 1) * TILE_SIZE
                entity_id, rect_item = create_static_obstacle(self.ecs, self.assets, x, self.highest_y, TILE_SIZE, "tree")
                self.addItem(rect_item)
                self.apply_debug_to_new_item(rect_item)
                self.obstacles.append(entity_id)
                
        elif lane_data.lane_type == LaneType.RIVER_LILY:
            for _ in range(random.randint(3, 6)):
                x = random.randint(0, (WINDOW_WIDTH // TILE_SIZE) - 1) * TILE_SIZE
                entity_id, rect_item = create_static_obstacle(self.ecs, self.assets, x, self.highest_y, TILE_SIZE, "lilypad")
                self.addItem(rect_item)
                self.apply_debug_to_new_item(rect_item)
                self.obstacles.append(entity_id)

    def update_world(self, camera_y):
        if self.highest_y > camera_y - WINDOW_HEIGHT:
            self.spawn_new_lane_row()

        cull_threshold = camera_y + (WINDOW_HEIGHT / 2) + (5 * TILE_SIZE)
        lanes_to_keep = []
        for lane_info in self.active_lanes_info:
            if lane_info[1] > cull_threshold:
                self.removeItem(lane_info[2]) 
            else:
                lanes_to_keep.append(lane_info)
        self.active_lanes_info = lanes_to_keep

        for lane_info in self.active_lanes_info:
            lane_data = lane_info[0]
            y_pos = lane_info[1]
            if lane_info[3] > 0: 
                lane_info[3] -= 1
                
            if lane_info[3] <= 0 and lane_data.lane_type in (LaneType.ROAD, LaneType.RIVER):
                if random.random() < (lane_data.spawn_rate / 2):
                    size_multiplier = random.choice([1, 2]) if lane_data.lane_type == LaneType.ROAD else random.choice([2, 3, 4])
                    width = TILE_SIZE * size_multiplier
                    start_x = -width if lane_data.direction == 1 else WINDOW_WIDTH
                    
                    entity_id, rect_item = create_obstacle(
                        self.ecs, self.assets, start_x, y_pos, width, TILE_SIZE,
                        lane_data.speed, lane_data.direction, lane_data.lane_type
                    )
                    self.addItem(rect_item)
                    self.apply_debug_to_new_item(rect_item)
                    self.obstacles.append(entity_id)

                    gap_behind = TILE_SIZE * random.uniform(2, 5) 
                    safe_speed = lane_data.speed if lane_data.speed > 0 else 1
                    lane_info[3] = int((width + gap_behind) / safe_speed)

        self.movement_system.update(self.ecs)
        self.render_system.update(self.ecs)

        active_obstacles = []
        for entity_id in self.obstacles:
            pos = self.ecs.get_component(entity_id, PositionComponent)
            render = self.ecs.get_component(entity_id, RenderComponent)
            
            if not pos or not render:
                continue
                
            vel = self.ecs.get_component(entity_id, VelocityComponent)
            out_of_bounds_x = False 
            
            if vel:
                direction = 1 if vel.vx > 0 else -1
                out_of_bounds_x = (direction == 1 and pos.x > WINDOW_WIDTH + 100) or \
                                  (direction == -1 and pos.x < -render.graphics_item.boundingRect().width() - 100)
            
            out_of_bounds_y = pos.y > cull_threshold

            if out_of_bounds_x or out_of_bounds_y:
                self.removeItem(render.graphics_item)
                self.ecs.destroy_entity(entity_id)
            else:
                active_obstacles.append(entity_id)
                
        self.obstacles = active_obstacles

    def reset(self):
        self.clear()
        self.active_lanes_info.clear()
        self.obstacles.clear()
        self.highest_y = WINDOW_HEIGHT
        self.generator = MapGenerator()
        
        for _ in range((WINDOW_HEIGHT // TILE_SIZE) + 2):
            self.spawn_new_lane_row()