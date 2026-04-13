from PyQt6.QtCore import QRectF
from config import TILE_SIZE, WINDOW_WIDTH, WINDOW_HEIGHT
from generator import LaneType
from ecs import PositionComponent, ColliderComponent, VelocityComponent
from events import CollisionEvent, GameOverEvent

class PhysicsEngine:
    def check_collisions(self, ecs_manager, player_entity_id, world_manager, camera_y, event_manager):
        player_pos = ecs_manager.get_component(player_entity_id, PositionComponent)
        player_col = ecs_manager.get_component(player_entity_id, ColliderComponent)
        if not player_pos or not player_col: 
            return

        if player_pos.y > camera_y + (WINDOW_HEIGHT / 2):
            event_manager.publish(CollisionEvent("screen"))
            event_manager.publish(GameOverEvent())
            return

        margin = 8
        player_hitbox = QRectF(
            player_pos.x + margin, player_pos.y + margin, 
            player_col.width - 2 * margin, player_col.height - 2 * margin
        )

        current_lane_type = LaneType.GRASS 
        player_center_y = player_pos.y + (player_col.height / 2)
        
        for lane_info in world_manager.active_lanes_info:
            if lane_info[1] <= player_center_y < lane_info[1] + TILE_SIZE:
                current_lane_type = lane_info[0].lane_type
                break

        on_log = False
        log_vx = 0

        for entity_id in ecs_manager.get_entities_with(PositionComponent, ColliderComponent):
            if entity_id == player_entity_id: 
                continue
                
            obs_pos = ecs_manager.get_component(entity_id, PositionComponent)
            obs_col = ecs_manager.get_component(entity_id, ColliderComponent)
            
            obs_hitbox = QRectF(obs_pos.x, obs_pos.y, obs_col.width, obs_col.height)
            
            if player_hitbox.intersects(obs_hitbox):
                if obs_col.tag == "car":
                    event_manager.publish(CollisionEvent("car"))
                    event_manager.publish(GameOverEvent())
                    return
                elif obs_col.tag == "tree":
                    player_pos.x = player_pos.prev_x
                    player_pos.y = player_pos.prev_y
                    return 
                elif obs_col.tag == "log":
                    on_log = True
                    vel = ecs_manager.get_component(entity_id, VelocityComponent)
                    if vel: 
                        log_vx = vel.vx
                elif obs_col.tag == "lilypad":
                    on_log = True
                    log_vx = 0

        if current_lane_type in (LaneType.RIVER, LaneType.RIVER_LILY):
            if on_log:
                player_pos.x += log_vx 
                if player_pos.x < -TILE_SIZE or player_pos.x > WINDOW_WIDTH:
                    event_manager.publish(CollisionEvent("screen"))
                    event_manager.publish(GameOverEvent())
            else:
                event_manager.publish(CollisionEvent("water"))
                event_manager.publish(GameOverEvent())