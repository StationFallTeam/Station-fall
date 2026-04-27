def _sanitize_runs(dungeon_runs):
    try:
        return max(0, int(dungeon_runs))
    except (TypeError, ValueError):
        return 0


def scale_enemy_health(base_health, dungeon_runs):
    runs = _sanitize_runs(dungeon_runs)
    multiplier = 1.0 + (0.15 * runs)
    return max(1, int(round(base_health * multiplier)))


def scale_enemy_damage(base_damage, dungeon_runs):
    runs = _sanitize_runs(dungeon_runs)
    multiplier = 1.0 + (0.10 * runs)
    return max(1, int(round(base_damage * multiplier)))
