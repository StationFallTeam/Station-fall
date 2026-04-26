import heapq

def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def is_walkable(collision_map, pos):
    return collision_map.get(pos, '#') == '.'

def get_neighbors(collision_map, pos):
    x, y = pos
    candidates = [
        (x + 1, y),
        (x - 1, y),
        (x, y + 1),
        (x, y - 1),
    ]
    return [p for p in candidates if is_walkable(collision_map, p)]

def reconstruct_path(came_from, current):
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path

def astar(collision_map, start, goal):
    if not is_walkable(collision_map, start) or not is_walkable(collision_map, goal):
        return []

    open_set = []
    heapq.heappush(open_set, (0, start))

    came_from = {}
    g_score = {start: 0}

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == goal:
            return reconstruct_path(came_from, current)

        for neighbor in get_neighbors(collision_map, current):
            tentative_g = g_score[current] + 1

            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                priority = tentative_g + heuristic(neighbor, goal)
                heapq.heappush(open_set, (priority, neighbor))

    return []

def world_to_tile(x, y, tile_size):
    return (int(x // tile_size), int(y // tile_size))

def tile_to_world_center(tx, ty, tile_size):
    return (
        tx * tile_size + tile_size // 2,
        ty * tile_size + tile_size // 2
    )