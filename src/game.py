import asyncio
import pygame

from src.background import SpaceBackground
from src.camera import Camera
from src.player import Player
from src.render import draw_objects, draw_pause_menu
from src.collision import handle_all_collisions, is_in_trigger
from src.inventory_ui import InventoryUI  

from dungeongen.classes import DungeonContext, CombatRoom
from dungeongen.loading import (
    create_hub_generator,
    create_dungeon_generator
)


async def game(win, settings=None):
    # Settings from main menu
    if settings is None:
        settings = {'music_volume': 0.5, 'brightness': 1.0}
    
    music_volume = settings.get('music_volume', 0.5)
    brightness = settings.get('brightness', 1.0)
    
    # Volume and brightness step constants
    VOLUME_STEP = 0.1
    BRIGHTNESS_STEP = 0.1
    screen_width = 920
    screen_height = 920

    pygame.display.set_caption("Station Fall")

    clock = pygame.time.Clock()
    game_font = pygame.font.SysFont("Pixellari.ttf", 25)

    background = SpaceBackground(screen_width, screen_height)
    camera = Camera(screen_width, screen_height)
    
    # Game objects
    bullets = []
    coins = []
    floating_texts = []
    inventory_ui = InventoryUI(screen_width, screen_height)
    
    # Game state
    inventory_state = False  # For inventory overlay
    paused = False # for pause menu - Wil
    
    hub_type = "hub"
    tile_size = 40  # 4 * 10 scaling factor
    
    # Create both generators
    hub_gen = create_hub_generator(hub_type)
    dungeon_gen = create_dungeon_generator()
    
    state = "hub"
    active_gen = hub_gen
    spawn = hub_gen.load_complete(tile_size)
    
    player = Player(spawn[0], spawn[1])
    
    room_count = 0
    completed_room_count = 0
    dungeon_context = DungeonContext(tile_size)
    
    last_player_tile = None
    
    running = True
    while running:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if paused:
                        paused = False
                    elif is_in_trigger(player, "quit"):
                        # Return current settings when quitting
                        current_settings = {'music_volume': music_volume, 'brightness': brightness}
                        return "quit", current_settings
                    else:
                        paused = not paused 
                
                # Settings controls
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    music_volume = min(music_volume + VOLUME_STEP, 1.0)
                    pygame.mixer.music.set_volume(music_volume)              
                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    music_volume = max(music_volume - VOLUME_STEP, 0.0)
                    pygame.mixer.music.set_volume(music_volume)               
                elif event.key == pygame.K_0:
                    brightness = min(brightness + BRIGHTNESS_STEP, 1.0)        
                elif event.key == pygame.K_9:
                    brightness = max(brightness - BRIGHTNESS_STEP, 0.2)
                        
                elif event.key == pygame.K_RETURN:
                    if state == "hub" and is_in_trigger(player, "start"):
                        # Transitiong to dungeon
                        state = "dungeon"
                        active_gen = dungeon_gen
                        spawn, dungeon_context = dungeon_gen.load_complete(tile_size)
                        current_money = player.money
                        player = Player(spawn[0], spawn[1])
                        player.money = current_money
                        bullets.clear()
                        floating_texts.clear()
                        last_player_tile = None
                        room_count, completed_room_count = dungeon_gen.get_room_counts()
                elif event.key == pygame.K_r and completed_room_count == room_count:
                    if state == "dungeon" and is_in_trigger(player, "leave"):
                        #Back to hub
                        state = "hub"
                        active_gen = hub_gen
                        spawn = hub_gen.load_complete(tile_size)
                        current_money = player.money
                        player = Player(spawn[0], spawn[1])
                        player.money = current_money
                        dungeon_context = DungeonContext(tile_size)
                        bullets.clear()
                        floating_texts.clear()
                        last_player_tile = None
                        room_count = 0
                        completed_room_count = 0
                elif event.key == pygame.K_i:
                    # Toggle inventory
                    inventory_state = not inventory_state
                        
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if paused:
                    if resume_rect.collidepoint(event.pos):
                        paused = False
                    elif menu_rect.collidepoint(event.pos):
                        current_settings = {'music_volume': music_volume, 'brightness': brightness}
                        return "menu", current_settings
                    elif quit_rect.collidepoint(event.pos):
                        current_settings = {'music_volume': music_volume, 'brightness': brightness}
                        return "quit", current_settings
                elif state == "dungeon":
                    # Shooting
                    mouse_world = camera.screen_to_world(event.pos)
                    bullet = player.shoot(mouse_world)
                    if bullet:
                        bullets.append(bullet)

        # Update phase
        if not paused:
            keys = pygame.key.get_pressed()
            
            # Player movement
            player.update(keys)
            camera.update(player)
            
            # Update floating texts
            floating_texts = [ft for ft in floating_texts if ft.update()]
        
            # Room-based combat system
            if state == "dungeon" and active_gen.rooms:
                # Check if player entered a new room
                player_tile_x = int(player.x // tile_size)
                player_tile_y = int(player.y // tile_size)
                current_player_tile = (player_tile_x, player_tile_y)
                
                if current_player_tile != last_player_tile:
                    last_player_tile = current_player_tile
                    
                    # Check if player is in any room's trigger area
                    for room in active_gen.rooms:
                        if (room.triggerRect.x <= player_tile_x < room.triggerRect.x + room.triggerRect.w and
                            room.triggerRect.y <= player_tile_y < room.triggerRect.y + room.triggerRect.h):
                            # Only combat rooms have on_enter logic
                            if isinstance(room, CombatRoom):
                                room.on_enter(dungeon_context)
                            break
                
                completed_room_count = 0
                # Update rooms for combat mechanics and get current room counts
                for room in active_gen.rooms:
                    # Only combat rooms need updates
                    if isinstance(room, CombatRoom):
                        room.update(dungeon_context)
                
                # Get updated room counts from dungeon
                room_count, completed_room_count = active_gen.get_room_counts()
                    
                # Update enemies  
                for enemy in dungeon_context.enemies[:]:
                    enemy.update(player.rect)
            
            # Update bullets
            for bullet in bullets[:]:
                bullet.update()
                # Remove bullets that are expired
                if bullet.is_dead():
                    bullets.remove(bullet)
            
            # Handle all collisions using the collision system 
            enemies_list = dungeon_context.enemies if state == "dungeon" else []
            handle_all_collisions(player, enemies_list, bullets, floating_texts, coins)
            
            # Check if player died
            if player.health <= 0:
                current_settings = {'music_volume': music_volume, 'brightness': brightness}
                return "dead", current_settings # Return to menu when player dies
                        
            # Update coins
            for coin in coins[:]:
                coin.update()
                if player.rect.colliderect(coin.rect):
                    player.money += coin.value
                    coins.remove(coin)

        win.fill((0, 0, 0))
        
        # Use the integrated render pipeline
        enemy_list = dungeon_context.enemies if state == "dungeon" else []
        draw_objects(
            win, player, enemy_list, bullets, camera, background, 
            coins, floating_texts, dungeon=active_gen, tile_size=tile_size
        )
        
        # Some text tips
        if state == "dungeon":
            progress_text = f"Rooms: {completed_room_count}/{room_count}"
            if completed_room_count == room_count:
                progress_text += " - Return to the spawn"
            text_surface = game_font.render(progress_text, True, (255, 255, 255))
            win.blit(text_surface, (20, 80))
            if is_in_trigger(player, "leave"):
                leave_text = "When you complete all rooms, press R to leave"
                leave_surface = game_font.render(leave_text, True, (255, 255, 0))
                win.blit(leave_surface, (20, 110))
        elif state == "hub":         
            if is_in_trigger(player, "start"):
                start_text = "Press ENTER to go to the next station"
                start_surface = game_font.render(start_text, True, (0, 255, 0))
                win.blit(start_surface, (20, 80))
            elif is_in_trigger(player, "info"):
                info_text = "Press [PLACEHOLDER] to read the help logs"
                info_surface = game_font.render(info_text, True, (0, 255, 255))
                win.blit(info_surface, (20, 80))
            elif is_in_trigger(player, "quit"):
                quit_text = "Press ESC to quit to menu"
                quit_surface = game_font.render(quit_text, True, (255, 255, 0))
                win.blit(quit_surface, (20, 80))
            elif is_in_trigger(player, "shop"):
                quit_text = "Press [PLACEHOLDER] to browse the shop"
                quit_surface = game_font.render(quit_text, True, (255, 255, 0))
                win.blit(quit_surface, (20, 80))
        
        # Draw inventory overlay if active
        if inventory_state:
            inventory_ui.draw(win, player.money)

        # Draw pause menu
        if paused:
            resume_rect, menu_rect, quit_rect = draw_pause_menu(win, screen_width, screen_height)
        else:
            resume_rect = menu_rect = quit_rect = pygame.Rect(0, 0, 0, 0)

        # Apply brightness filter
        if brightness < 1.0:
            dark_surface = pygame.Surface((screen_width, screen_height))
            dark_surface.set_alpha(int((1.0 - brightness) * 255))
            dark_surface.fill((0, 0, 0))
            win.blit(dark_surface, (0, 0))
            
        pygame.display.flip()
        await asyncio.sleep(0)

