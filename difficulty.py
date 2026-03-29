from config import TILE_SIZE, WINDOW_WIDTH, WINDOW_HEIGHT

class DifficultyManager:
    def __init__(self):
        self.camera_speed = 0.5        
        self.camera_accel = 0.0001
        self.max_camera_speed = 3.5
        
        self.obstacle_speed_multiplier = 1.0
        self.spawn_rate_multiplier = 1.0
        
        self.starting_y = WINDOW_HEIGHT - (4 * TILE_SIZE)
        self.current_score = 0

    def update(self, current_camera_y):
        if self.camera_speed < self.max_camera_speed:
            self.camera_speed += self.camera_accel

        distance_traveled = self.starting_y - current_camera_y
        self.current_score = int(distance_traveled / TILE_SIZE)

        difficulty_level = self.current_score // 50
        
        self.obstacle_speed_multiplier = 1.0 + (difficulty_level * 0.1)
        self.spawn_rate_multiplier = 1.0 + (difficulty_level * 0.1)
        
        if self.obstacle_speed_multiplier > 2.5: 
            self.obstacle_speed_multiplier = 2.5
        if self.spawn_rate_multiplier > 2.0:
            self.spawn_rate_multiplier = 2.0

    def apply_to_lane_data(self, lane_data):
        lane_data.speed *= self.obstacle_speed_multiplier
        lane_data.spawn_rate *= self.spawn_rate_multiplier
        return lane_data
    
    def reset(self):
        self.camera_speed = 0.5        
        self.obstacle_speed_multiplier = 1.0
        self.spawn_rate_multiplier = 1.0
        self.current_score = 0