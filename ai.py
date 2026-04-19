import math
import random
from PyQt6.QtCore import QRectF
from config import TILE_SIZE, WINDOW_WIDTH, SETTINGS
from ecs import PositionComponent, ColliderComponent, VelocityComponent, AIComponent
from generator import LaneType

class AISystem:
    def __init__(self):
        self.bot_history = {}
        self.max_history_len = 16

    def update(self, ecs, world_manager):
        trees, cars, platforms = self.scan_world(ecs, world_manager)

        for ent_id, components in ecs.entities.items():
            ai = ecs.get_component(ent_id, AIComponent)
            pos = ecs.get_component(ent_id, PositionComponent)
            if not ai or not pos: continue

            if ent_id not in self.bot_history:
                self.bot_history[ent_id] = []

            self.apply_platform_momentum(pos, platforms)

            ai.timer += 1
            if ai.timer < SETTINGS.data["ai_move_delay"]: continue
            ai.timer = 0

            snapped_x = round(pos.x / TILE_SIZE) * TILE_SIZE
            history = self.bot_history[ent_id]
            best_move = self.find_best_move(snapped_x, pos.y, trees, cars, platforms, world_manager, history)

            if best_move:
                if best_move[1] < pos.y: ai.state = "RACING"
                elif best_move[1] > pos.y: ai.state = "BACKTRACKING"
                elif best_move[0] != pos.x: ai.state = "ALIGNING_TO_TARGET"
                else: ai.state = "WAITING_SAFELY" 
                
                pos.x, pos.y = best_move

                self.bot_history[ent_id].append(best_move)
                if len(self.bot_history[ent_id]) > self.max_history_len:
                    self.bot_history[ent_id].pop(0)

    def scan_world(self, ecs, world_manager):
        trees, cars, platforms = [], [], []
        for ent_id in world_manager.obstacles:
            p = ecs.get_component(ent_id, PositionComponent)
            c = ecs.get_component(ent_id, ColliderComponent)
            v = ecs.get_component(ent_id, VelocityComponent)
            if p and c:
                if c.tag == "tree": trees.append((p, c))
                elif c.tag in ["car", "truck"]: cars.append((p, c))
                elif c.tag in ["log", "lilypad"]: platforms.append((p, c, v.vx if v else 0))
        return trees, cars, platforms

    def apply_platform_momentum(self, pos, platforms):
        hitbox = QRectF(pos.x + 8, pos.y + 8, TILE_SIZE - 16, TILE_SIZE - 16)
        for p_pos, p_col, vx in platforms:
            if hitbox.intersects(QRectF(p_pos.x, p_pos.y, p_col.width, p_col.height)):
                pos.x += vx
                return

    def find_best_move(self, cur_x, cur_y, trees, cars, platforms, world, history):
        LOOKAHEAD_DEPTH = 5
        
        possible_moves = [
            (cur_x, cur_y - TILE_SIZE),
            (cur_x - TILE_SIZE, cur_y),
            (cur_x + TILE_SIZE, cur_y),
            (cur_x, cur_y),
            (cur_x, cur_y + TILE_SIZE)
        ]
        
        best_move = None
        best_score = -float('inf')

        blocked_up = not self.is_safe(cur_x, cur_y - TILE_SIZE, trees, cars, platforms, world)

        for nx, ny in possible_moves:
            if self.is_safe(nx, ny, trees, cars, platforms, world):
                score = self.evaluate_path(nx, ny, LOOKAHEAD_DEPTH - 1, trees, cars, platforms, world)

                if ny < cur_y: score += 50
                elif ny > cur_y: score -= 50
                elif ny == cur_y and nx == cur_x: score -= 10

                if blocked_up and ny == cur_y and nx != cur_x:
                    score += 30 
                
                score += self.get_strategic_score(nx, ny, cur_x, cur_y, platforms, trees, world)
                center_x = WINDOW_WIDTH / 2
                score -= (abs(nx - center_x) * 0.05) 

                visit_count = history.count((nx, ny))
                if visit_count > 0: score -= (visit_count * 150)
                score += random.uniform(0, 2)
                
                if score > best_score:
                    best_score = score
                    best_move = (nx, ny)

        return best_move

    def get_strategic_score(self, nx, ny, cur_x, cur_y, platforms, trees, world):
        score = 0
        for i in range(1, 4):
            scan_y = cur_y - (i * TILE_SIZE)
            lane = self.get_lane_at(scan_y, world)
            
            if lane:
                if lane.lane_type in (LaneType.RIVER, LaneType.RIVER_LILY):
                    target_x = self.find_nearest_platform_x(nx, scan_y, cur_y, platforms, trees)
                    if target_x is not None:
                        dist_before = abs(cur_x - target_x)
                        dist_after = abs(nx - target_x)
                        if dist_after < dist_before:
                            score += 80 
                    break 
        return score

    def find_nearest_platform_x(self, x, target_y, cur_y, platforms, trees):
        nearest_x = None
        min_dist = float('inf')
        for p_pos, p_col, _ in platforms:
            if abs(p_pos.y - target_y) < 5:
                is_blocked = False
                for t_pos, t_col in trees:
                    if abs(t_pos.x - p_pos.x) < 5 and target_y < t_pos.y < cur_y:
                        is_blocked = True
                        break
                if is_blocked: continue

                dist = abs(p_pos.x - x)
                if dist < min_dist:
                    min_dist = dist
                    nearest_x = p_pos.x + (p_col.width / 2)
        return nearest_x

    def evaluate_path(self, x, y, depth, trees, cars, platforms, world):
        if depth == 0:
            return -y
            
        possible_moves = [(x, y - TILE_SIZE), (x - TILE_SIZE, y), (x + TILE_SIZE, y), (x, y)]
        max_score = -float('inf')
        has_safe = False
        
        for nx, ny in possible_moves:
            if self.is_safe(nx, ny, trees, cars, platforms, world):
                has_safe = True
                score = self.evaluate_path(nx, ny, depth - 1, trees, cars, platforms, world)
                if score > max_score:
                    max_score = score
                    
        if not has_safe: return -float('inf')
        return max_score

    def get_lane_at(self, y, world):
        for lane_info in world.active_lanes_info:
            if lane_info[1] <= y < lane_info[1] + TILE_SIZE: return lane_info[0]
        return None

    def is_safe(self, tx, ty, trees, cars, platforms, world):
        if tx < 0 or tx >= WINDOW_WIDTH: return False
        
        margin = 5
        hitbox = QRectF(tx + margin, ty + margin, TILE_SIZE - 2*margin, TILE_SIZE - 2*margin)
        
        for tp, tc in trees:
            if hitbox.intersects(QRectF(tp.x, tp.y, tc.width, tc.height)): return False
            
        lane = self.get_lane_at(ty, world)
        if not lane: return True
        
        if lane.lane_type in (LaneType.RIVER, LaneType.RIVER_LILY):
            on_p = any(hitbox.intersects(QRectF(pp.x, pp.y, pc.width, pc.height)) for pp, pc, _ in platforms)
            if not on_p: return False
            
        if lane.lane_type == LaneType.ROAD:
            for cp, cc in cars:
                if abs(cp.y - ty) < 5:
                    danger_zone = QRectF(cp.x - TILE_SIZE * 1.5, cp.y, cc.width + TILE_SIZE*3, cc.height)
                    if hitbox.intersects(danger_zone): return False
                    
        return True