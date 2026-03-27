class EventManager:
    def __init__(self):
        self.listeners = {}

    def subscribe(self, event_type: str, listener_func):
        """Zapisuje funkcję do nasłuchiwania konkretnego zdarzenia."""
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(listener_func)

    def emit(self, event_type: str, **kwargs):
        """Wysyła zdarzenie w eter z dodatkowymi danymi (kwargs)."""
        if event_type in self.listeners:
            for listener in self.listeners[event_type]:
                listener(**kwargs)

class LoggerSystem:
    def __init__(self, event_manager: EventManager):
        event_manager.subscribe("PLAYER_MOVED", self.on_player_moved)
        event_manager.subscribe("GAME_OVER", self.on_game_over)
        event_manager.subscribe("MAP_GENERATED", self.on_map_generated)

    def on_player_moved(self, direction, new_x, new_y):
        print(f"[LOGGER] Ruch {direction} -> Pozycja: ({new_x}, {new_y})")

    def on_game_over(self, reason):
        print(f"[LOGGER] KONIEC GRY! Powód: {reason}")
        
    def on_map_generated(self, chunk_y):
        print(f"[LOGGER] Wygenerowano nowy fragment mapy na wysokości Y: {chunk_y}")