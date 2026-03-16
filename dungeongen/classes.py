"""Data classes for dungeon generation."""


class Rect:
    """A rectangle with position and size."""
    
    def __init__(self, x: int, y: int, w: int, h: int):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
    
    @property
    def right(self) -> int:
        """Right edge x-coordinate (inclusive)."""
        return self.x + self.w - 1
    
    @property
    def bottom(self) -> int:
        """Bottom edge y-coordinate (inclusive)."""
        return self.y + self.h - 1
    
    @property
    def center(self) -> tuple[int, int]:
        """Center point of the rectangle."""
        return (self.x + self.w // 2, self.y + self.h // 2)


class Prefab:
    """A prefab with collision, obstacle, and base layers."""
    
    def __init__(self, collision: list[str], obstacle: list[str], base: list[str]):
        self.collision = collision
        self.obstacle = obstacle
        self.base = base


class Room:
    """A room in the dungeon."""
    
    def __init__(self, rect: Rect, prefab_id: int | None = None, is_base_room: bool = False):
        self.rect = rect
        self.prefab_id = prefab_id
        self.is_base_room = is_base_room
        self.wall_prefab_id: int | None = None
        self.doors: list[tuple[int, int]] = []
    
    @property
    def center(self) -> tuple[int, int]:
        """Center point of the room (delegates to rect)."""
        return self.rect.center


class Hallway:
    """A hallway connecting rooms."""
    
    def __init__(self, rect: Rect, direction: str, prefab_id: int | None = None):
        self.rect = rect
        self.direction = direction
        self.prefab_id = prefab_id
        self.wall_prefab_id: int | None = None


# Type alias for tile map
TileMap = dict[tuple[int, int], str]
