import math
from ecs import PositionComponent, ColliderComponent, AIComponent

class AISystem:
    def update(self, ecs, player_entity):
        player_pos = ecs.get_component(player_entity, PositionComponent)
        if not player_pos: 
            return

        obstacles = []
        for ent_id in list(ecs.entities.keys()):
            col = ecs.get_component(ent_id, ColliderComponent)
            if col and col.tag == "obstacle":
                p = ecs.get_component(ent_id, PositionComponent)
                if p: obstacles.append(p)

        for ent_id in list(ecs.entities.keys()):
            ai = ecs.get_component(ent_id, AIComponent)
            pos = ecs.get_component(ent_id, PositionComponent)
            if not ai or not pos: 
                continue

            dist_to_player = math.hypot(player_pos.x - pos.x, player_pos.y - pos.y)
            
            closest_car_dist = float('inf')
            closest_car = None
            for obs in obstacles:
                d = math.hypot(obs.x - pos.x, obs.y - pos.y)
                if d < closest_car_dist:
                    closest_car_dist = d
                    closest_car = obs

            if closest_car_dist < 100:
                ai.state = "EVADE"
            elif dist_to_player < 300:
                ai.state = "CHASE"
            else:
                ai.state = "IDLE"

            if ai.state == "CHASE":
                dx = player_pos.x - pos.x
                dy = player_pos.y - pos.y
                dist = math.hypot(dx, dy)
                if dist > 0:
                    pos.x += (dx / dist) * ai.speed
                    pos.y += (dy / dist) * ai.speed

            elif ai.state == "EVADE" and closest_car:
                dx = pos.x - closest_car.x
                dy = pos.y - closest_car.y
                dist = math.hypot(dx, dy)
                if dist > 0:
                    pos.x += (dx / dist) * ai.speed
                    pos.y += (dy / dist) * ai.speed