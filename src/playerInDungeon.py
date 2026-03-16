import asyncio
import os
import random
import sys
import time
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

from config import (
	ALLOW_HALLWAY_THROUGH_ROOMS,
	BASE_ROOM_SIZE,
	BRANCH_FROM_SIDE_DECAY,
	BRANCH_FROM_SIDE_START_CHANCE,
	BRANCH_FROM_TOP_BOTTOM_DECAY,
	BRANCH_FROM_TOP_BOTTOM_START_CHANCE,
	GENERATE_VERTICAL_FIRST,
	HALL_LENGTH,
	HALL_THICKNESS,
	ROOM_SIZE,
	SIDE_DECAY,
	SIDE_START_CHANCE,
	TOP_BOTTOM_DECAY,
	TOP_BOTTOM_START_CHANCE,
)
from generation import generate_layout
from loading import (
	find_dungeon_types,
	find_presets,
	load_all_hallway_prefabs,
	load_all_hallway_wall_prefabs,
	load_main_room_prefabs,
	load_main_room_wall_prefabs,
	load_prefabs,
	load_preset,
	load_sprites_for_dungeon_type,
	load_wall_prefabs,
)
from rendering import draw_grid


def apply_preset(preset: dict, params: dict) -> None:
	keys = [
		"SIDE_START_CHANCE",
		"SIDE_DECAY",
		"BRANCH_FROM_SIDE_START_CHANCE",
		"BRANCH_FROM_SIDE_DECAY",
		"TOP_BOTTOM_START_CHANCE",
		"TOP_BOTTOM_DECAY",
		"BRANCH_FROM_TOP_BOTTOM_START_CHANCE",
		"BRANCH_FROM_TOP_BOTTOM_DECAY",
		"GENERATE_VERTICAL_FIRST",
		"ALLOW_HALLWAY_THROUGH_ROOMS",
	]
	for key in keys:
		if key in preset:
			params[key] = preset[key]


def collision_map_to_walls(collision_map: dict[tuple[int, int], str], tile_size: int) -> list[pygame.Rect]:
	walls: list[pygame.Rect] = []
	for (tile_x, tile_y), value in collision_map.items():
		if value != ".":
			walls.append(
				pygame.Rect(
					tile_x * tile_size,
					tile_y * tile_size,
					tile_size,
					tile_size,
				)
			)
	return walls


def generate_dungeon(tile_size: int) -> dict:
	params = {
		"SIDE_START_CHANCE": SIDE_START_CHANCE,
		"SIDE_DECAY": SIDE_DECAY,
		"BRANCH_FROM_SIDE_START_CHANCE": BRANCH_FROM_SIDE_START_CHANCE,
		"BRANCH_FROM_SIDE_DECAY": BRANCH_FROM_SIDE_DECAY,
		"TOP_BOTTOM_START_CHANCE": TOP_BOTTOM_START_CHANCE,
		"TOP_BOTTOM_DECAY": TOP_BOTTOM_DECAY,
		"BRANCH_FROM_TOP_BOTTOM_START_CHANCE": BRANCH_FROM_TOP_BOTTOM_START_CHANCE,
		"BRANCH_FROM_TOP_BOTTOM_DECAY": BRANCH_FROM_TOP_BOTTOM_DECAY,
		"GENERATE_VERTICAL_FIRST": GENERATE_VERTICAL_FIRST,
		"ALLOW_HALLWAY_THROUGH_ROOMS": ALLOW_HALLWAY_THROUGH_ROOMS,
	}

	available_types = find_dungeon_types(str(DUNGEON_TYPES_DIR))
	available_presets = find_presets(str(DUNGEON_PRESETS_DIR))

	if not available_types:
		raise RuntimeError("No valid dungeon types found in dungeongen/dungeon_types")

	dungeon_type = random.choice(available_types)
	preset_name = random.choice(available_presets) if available_presets else "default"
	if available_presets:
		preset = load_preset(preset_name, str(DUNGEON_PRESETS_DIR))
		apply_preset(preset, params)

	prefabs = load_prefabs(dungeon_type, str(DUNGEON_TYPES_DIR))
	wall_prefabs = load_wall_prefabs(dungeon_type, str(DUNGEON_TYPES_DIR))
	main_room_prefabs = load_main_room_prefabs(dungeon_type, str(DUNGEON_TYPES_DIR))
	main_room_wall_prefabs = load_main_room_wall_prefabs(dungeon_type, str(DUNGEON_TYPES_DIR))
	hallway_prefabs = load_all_hallway_prefabs(dungeon_type, str(DUNGEON_TYPES_DIR))
	hallway_wall_prefabs = load_all_hallway_wall_prefabs(dungeon_type, str(DUNGEON_TYPES_DIR))
	sprites = load_sprites_for_dungeon_type(dungeon_type, str(DUNGEON_TYPES_DIR))

	seed = time.time_ns()
	tiles, rooms, hallways, collision_map = generate_layout(
		base_room_size=BASE_ROOM_SIZE,
		room_size=ROOM_SIZE,
		hall_length=HALL_LENGTH,
		hall_thickness=HALL_THICKNESS,
		seed=seed,
		prefabs=prefabs,
		wall_prefabs=wall_prefabs,
		main_room_prefabs=main_room_prefabs,
		main_room_wall_prefabs=main_room_wall_prefabs,
		hallway_prefabs_upways=hallway_prefabs["upways"],
		hallway_prefabs_sideways=hallway_prefabs["sideways"],
		hallway_wall_prefabs_sideways=hallway_wall_prefabs["sideways"],
		side_start_chance=params["SIDE_START_CHANCE"],
		side_decay=params["SIDE_DECAY"],
		branch_from_side_start_chance=params["BRANCH_FROM_SIDE_START_CHANCE"],
		branch_from_side_decay=params["BRANCH_FROM_SIDE_DECAY"],
		top_bottom_start_chance=params["TOP_BOTTOM_START_CHANCE"],
		top_bottom_decay=params["TOP_BOTTOM_DECAY"],
		branch_from_top_bottom_start_chance=params["BRANCH_FROM_TOP_BOTTOM_START_CHANCE"],
		branch_from_top_bottom_decay=params["BRANCH_FROM_TOP_BOTTOM_DECAY"],
		generate_vertical_first=params["GENERATE_VERTICAL_FIRST"],
		allow_hallway_through_rooms=params["ALLOW_HALLWAY_THROUGH_ROOMS"],
	)

	walls = collision_map_to_walls(collision_map, tile_size)

	base_room = next((room for room in rooms if room.is_base_room), None)
	if base_room is None:
		spawn_tile = (0, 0)
	else:
		spawn_tile = base_room.center

	spawn_position = (
		spawn_tile[0] * tile_size,
		spawn_tile[1] * tile_size,
	)

	return {
		"walls": walls,
		"spawn_position": spawn_position,
		"dungeon_type": dungeon_type,
		"preset_name": preset_name,
		"tiles": tiles,
		"rooms": rooms,
		"hallways": hallways,
		"prefabs": prefabs,
		"wall_prefabs": wall_prefabs,
		"main_room_prefabs": main_room_prefabs,
		"main_room_wall_prefabs": main_room_wall_prefabs,
		"hallway_prefabs_upways": hallway_prefabs["upways"],
		"hallway_prefabs_sideways": hallway_prefabs["sideways"],
		"hallway_wall_prefabs_sideways": hallway_wall_prefabs["sideways"],
		"sprites": sprites,
	}


async def main() -> None:
	os.chdir(str(PROJECT_ROOT))
	pygame.init()

	screen_width = 1280
	screen_height = 720
	tile_size = 48
	win = pygame.display.set_mode((screen_width, screen_height))
	pygame.display.set_caption("Station Fall - Dungeon Mode")

	clock = pygame.time.Clock()
	font = pygame.font.SysFont("consolas", 24)

	background = SpaceBackground(screen_width, screen_height)
	camera = Camera(screen_width, screen_height)

	dungeon = generate_dungeon(tile_size)
	walls = dungeon["walls"]
	spawn_position = dungeon["spawn_position"]
	dungeon_type = dungeon["dungeon_type"]
	preset_name = dungeon["preset_name"]

	player = Player(spawn_position[0], spawn_position[1])
	bullets = []
	enemies = []

	running = True
	while running:
		clock.tick(60)

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False

			elif event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					running = False
				elif event.key == pygame.K_r:
					dungeon = generate_dungeon(tile_size)
					walls = dungeon["walls"]
					spawn_position = dungeon["spawn_position"]
					dungeon_type = dungeon["dungeon_type"]
					preset_name = dungeon["preset_name"]
					player = Player(spawn_position[0], spawn_position[1])
					bullets.clear()

			elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
				mouse_screen = pygame.mouse.get_pos()
				mouse_world = camera.screen_to_world(mouse_screen)
				bullet = player.shoot(mouse_world)
				if bullet is not None:
					bullets.append(bullet)

		keys = pygame.key.get_pressed()
		player.update(keys, walls)

		for bullet in bullets[:]:
			bullet.update()
			if bullet.is_dead():
				bullets.remove(bullet)

		camera.update(player)
		background.update_and_draw(win, (camera.camera.x, camera.camera.y))
		draw_grid(
			surface=win,
			tiles=dungeon["tiles"],
			tile_size=tile_size,
			cam_x=-camera.camera.x,
			cam_y=-camera.camera.y,
			show_grid=False,
			screen_w=screen_width,
			screen_h=screen_height,
			rooms=dungeon["rooms"],
			hallways=dungeon["hallways"],
			prefabs=dungeon["prefabs"],
			wall_prefabs=dungeon["wall_prefabs"],
			main_room_prefabs=dungeon["main_room_prefabs"],
			main_room_wall_prefabs=dungeon["main_room_wall_prefabs"],
			hallway_prefabs_upways=dungeon["hallway_prefabs_upways"],
			hallway_prefabs_sideways=dungeon["hallway_prefabs_sideways"],
			hallway_wall_prefabs_sideways=dungeon["hallway_wall_prefabs_sideways"],
			sprites=dungeon["sprites"],
			show_sprites=True,
		)

		player.draw(win, camera)
		for enemy in enemies:
			enemy.draw(win, camera)
		for bullet in bullets:
			bullet.draw(win, camera)

		draw_health_bar(win, player.health, player.max_health, 20, 20, 250, 18)

		mode_text = font.render(
			f"Dungeon type: {dungeon_type} | Preset: {preset_name} | R = regenerate",
			True,
			(255, 255, 255),
		)
		win.blit(mode_text, (18, 18))

		pygame.display.flip()
		await asyncio.sleep(0)

	pygame.quit()


if __name__ == "__main__":
	asyncio.run(main())
