import logging

class PlayerMovedEvent:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class CollisionEvent:
    def __init__(self, tag):
        self.tag = tag

class TogglePauseEvent:
    pass

class GameOverEvent:
    pass

class ReloadConfigEvent: 
    pass

class EventManager:
    def __init__(self):
        self.listeners = {}

    def subscribe(self, event_type: str, listener):
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(listener)

    def publish(self, event):
        event_type = type(event).__name__
        if event_type in self.listeners:
            for listener in self.listeners[event_type]:
                listener(event)


class LoggerSystem:
    def __init__(self, event_manager):
        self.event_manager = event_manager
        
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
            
        logging.basicConfig(
            filename='game.log', 
            level=logging.INFO, 
            format='%(asctime)s [%(levelname)s] %(message)s', 
            filemode='w'
        )
        
        self.event_manager.subscribe("PlayerMovedEvent", self.log_movement)
        self.event_manager.subscribe("CollisionEvent", self.log_collision)

    def log_movement(self, event):
        logging.info(f"Move: {event.x}, {event.y}")

    def log_collision(self, event):
        logging.warning(f"Collision: {event.tag}")

