import asyncio
import os
import sys
from pathlib import Path

import pygame

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if __package__ in (None, ""):
	if str(PROJECT_ROOT) not in sys.path:
		sys.path.insert(0, str(PROJECT_ROOT))
	from src.background import SpaceBackground
	from src.camera import Camera
	from src.player import Player
	from src.ui import draw_health_bar
else:
	from .background import SpaceBackground
	from .camera import Camera
	from .player import Player
	from .ui import draw_health_bar


DUNGEONGEN_DIR = Path(__file__).resolve().parents[1] / "dungeongen"
DUNGEON_TYPES_DIR = DUNGEONGEN_DIR / "dungeon_types"
DUNGEON_PRESETS_DIR = DUNGEONGEN_DIR / "dungeon_gen_presets"
if str(DUNGEONGEN_DIR) not in sys.path:
	sys.path.insert(0, str(DUNGEONGEN_DIR))

from classes import DungeonGen, HubGen


def _hub_spawn(hub: HubGen, tile_size: int):
	if hub.rooms:
		cx, cy = hub.rooms[0].center
		return (cx * tile_size, cy * tile_size)
	return (0, 0)


def _dungeon_spawn(dungeon: DungeonGen, tile_size: int):
	base_room = next((r for r in dungeon.rooms if r.is_base_room), None)
	if base_room is None:
		return (0, 0)
	return (base_room.center[0] * tile_size, base_room.center[1] * tile_size)


TILE_SIZE = 40


def _make_hub(hub_type: str):
	hub = HubGen(hub_path=str(DUNGEON_TYPES_DIR / hub_type))
	hub.loadAllAssets()
	hub.generateHubRoom()
	walls = hub.getCollisionRects(tile_size=TILE_SIZE)
	return hub, walls


def _make_dungeon():
	dungeon = DungeonGen(
		base_path=str(DUNGEON_TYPES_DIR),
		preset_directory=str(DUNGEON_PRESETS_DIR),
	)
	dungeon.generateDungeonRandom()
	walls = dungeon.getCollisionRects(tile_size=TILE_SIZE)
	return dungeon, walls


async def main():
	os.chdir(str(PROJECT_ROOT))
	pygame.init()

	screen_width = 1280
	screen_height = 720
	tile_size = TILE_SIZE
	win = pygame.display.set_mode((screen_width, screen_height))
	pygame.display.set_caption("Station Fall")

	clock = pygame.time.Clock()
	font = pygame.font.SysFont("consolas", 24)

	background = SpaceBackground(screen_width, screen_height)
	camera = Camera(screen_width, screen_height)

	# --- start in hub ---
	hub_type = sorted(os.listdir(str(DUNGEON_TYPES_DIR)))[0]
	state = "hub"
	active_gen, walls = _make_hub(hub_type)
	spawn = _hub_spawn(active_gen, tile_size)
	player = Player(spawn[0], spawn[1])
	hud_text = f"Hub | ENTER = enter dungeon"

	running = True
	while running:
		clock.tick(60)

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False

			elif event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					running = False

				elif event.key == pygame.K_RETURN:
					# ENTER: jump into a random dungeon
					state = "dungeon"
					active_gen, walls = _make_dungeon()
					spawn = _dungeon_spawn(active_gen, tile_size)
					player = Player(spawn[0], spawn[1])
					dtype = active_gen.dungeon_type or "unknown"
					preset = active_gen.preset_name or "default"
					hud_text = f"{dtype} | {preset} | ENTER = new dungeon | R = hub"

				elif event.key == pygame.K_r:
					if state == "dungeon":
						# R in dungeon: back to hub
						state = "hub"
						active_gen, walls = _make_hub(hub_type)
						spawn = _hub_spawn(active_gen, tile_size)
						player = Player(spawn[0], spawn[1])
						hud_text = f"Hub | ENTER = enter dungeon"

		keys = pygame.key.get_pressed()
		player.update(keys, walls)

		camera.update(player)
		background.update_and_draw(win, (camera.camera.x, camera.camera.y))
		active_gen.draw(
			surface=win,
			tile_size=tile_size,
			cam_x=-camera.camera.x,
			cam_y=-camera.camera.y,
			show_grid=False,
			show_sprites=True,
		)

		player.draw(win, camera)

		win.blit(font.render(hud_text, True, (255, 255, 255)), (18, 18))

		pygame.display.flip()
		await asyncio.sleep(0)

	pygame.quit()


if __name__ == "__main__":
	asyncio.run(main())
