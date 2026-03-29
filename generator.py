import random
from enum import Enum
from dataclasses import dataclass

class LaneType(Enum):
    GRASS = "Grass"   
    ROAD = "Road"    
    RIVER = "River"   
    RIVER_LILY = "River_Lily"

@dataclass
class LaneData:
    lane_type: LaneType
    direction: int
    speed: float
    spawn_rate: float

class MapGenerator:
    def __init__(self):
        self.lane_history = [] 

    def generate_initial_map(self, num_lanes=20):
        lanes = []
        for i in range(num_lanes):
            if i < 3:
                lane = LaneData(LaneType.GRASS, 0, 0.0, 0.0)
            else:
                lane = self.generate_single_lane()
            self.lane_history.append(lane.lane_type)
            lanes.append(lane)
        return lanes

    def generate_next_lane(self) -> LaneData:
        lane = self.generate_single_lane()
        self.lane_history.append(lane.lane_type)
        if len(self.lane_history) > 10:
            self.lane_history.pop(0)
        return lane

    def generate_single_lane(self) -> LaneData:
        last_1 = self.lane_history[-1] if len(self.lane_history) >= 1 else None
        last_2 = self.lane_history[-2] if len(self.lane_history) >= 2 else None
        last_3 = self.lane_history[-3] if len(self.lane_history) >= 3 else None

        allowed_types = [LaneType.GRASS, LaneType.ROAD, LaneType.RIVER, LaneType.RIVER_LILY]

        if last_1 in (LaneType.RIVER, LaneType.RIVER_LILY):
            allowed_types.remove(LaneType.RIVER)
            if LaneType.RIVER_LILY in allowed_types: 
                allowed_types.remove(LaneType.RIVER_LILY)

        if last_1 == LaneType.ROAD and last_2 == LaneType.ROAD and last_3 == LaneType.ROAD:
            allowed_types.remove(LaneType.ROAD)

        chosen_type = random.choice(allowed_types)

        direction = 0
        speed = 0.0
        spawn_rate = 0.0

        if chosen_type in (LaneType.ROAD, LaneType.RIVER):
            direction = random.choice([-1, 1]) 
            speed = random.uniform(1.0, 3.0) 
            spawn_rate = random.uniform(0.01, 0.03)

        return LaneData(chosen_type, direction, speed, spawn_rate)