from PyQt6.QtCore import QRectF
from game.generator import LaneType
from engine.world import TILE_SIZE, WINDOW_WIDTH, WINDOW_HEIGHT
from engine.ecs import PositionComponent, ColliderComponent, VelocityComponent

class PhysicsEngine:
    def __init__(self):
        self.is_game_over = False

    def check_collisions(self, ecs_manager, player_entity_id, world_manager, camera_y, event_manager):
        if self.is_game_over: return

        player_pos = ecs_manager.get_component(player_entity_id, PositionComponent)
        player_col = ecs_manager.get_component(player_entity_id, ColliderComponent)
        
        if not player_pos or not player_col: return

        if player_pos.y > camera_y + (WINDOW_HEIGHT / 2):
            event_manager.emit("GAME_OVER", reason="Zbyt wolno! Zjadła Cię kamera.") # <--- ZMIANA
            self.is_game_over = True
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
            if entity_id == player_entity_id: continue
                
            obs_pos = ecs_manager.get_component(entity_id, PositionComponent)
            obs_col = ecs_manager.get_component(entity_id, ColliderComponent)
            
            obs_hitbox = QRectF(obs_pos.x, obs_pos.y, obs_col.width, obs_col.height)
            
            if player_hitbox.intersects(obs_hitbox):
                if obs_col.tag == "car":
                    event_manager.emit("GAME_OVER", reason="Przejechał Cię samochód!")
                    self.is_game_over = True
                    return
                elif obs_col.tag == "tree":
                    # --- NOWE: Ściana. Cofamy gracza do poprzedniej pozycji! ---
                    player_pos.x = player_pos.prev_x
                    player_pos.y = player_pos.prev_y
                    # Przerwij sprawdzanie reszty, żeby nie zginął przez przypadek
                    return 
                elif obs_col.tag == "log":
                    on_log = True
                    vel = ecs_manager.get_component(entity_id, VelocityComponent)
                    if vel: log_vx = vel.vx
                elif obs_col.tag == "lilypad":
                    # --- NOWE: Stoi na bezpiecznej lilii, nie porusza się ---
                    on_log = True
                    log_vx = 0

        # Zaktualizowana logika tonięcia (uwzględnia nowy typ rzeki)
        if current_lane_type in (LaneType.RIVER, LaneType.RIVER_LILY):
            if on_log:
                player_pos.x += log_vx 
                if player_pos.x < -TILE_SIZE or player_pos.x > WINDOW_WIDTH:
                    event_manager.emit("GAME_OVER", reason="Wypłynąłeś poza ekran!")
                    self.is_game_over = True
            else:
                event_manager.emit("GAME_OVER", reason="Wpadłeś do wody i utonąłeś!")
                self.is_game_over = True