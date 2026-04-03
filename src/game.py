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


async def game(win):
    screen_width = 920
    screen_height = 920

    pygame.display.set_caption("Station Fall")

    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 24)

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
                        paused = False          # resume
                    elif is_in_trigger(player, "quit"):
                        return "quit"
                    else:
                        paused = not paused     # open pause menu
                        
                elif event.key == pygame.K_RETURN:
                    if state == "hub":
                        # Check if player is in start trigger
                        if is_in_trigger(player, "start"):
                            # Transitiong to dungeon
                            state = "dungeon"
                            active_gen = dungeon_gen
                            
                            # Load dungeon
                            spawn, dungeon_context = dungeon_gen.load_complete(tile_size)
                                
                            # Preserve player money and respawn
                            current_money = player.money
                            player = Player(spawn[0], spawn[1])
                            player.money = current_money
                                
                            # Clear previous state
                            bullets.clear()
                            floating_texts.clear()
                            last_player_tile = None

                            room_count, completed_room_count = dungeon_gen.get_room_counts()

                elif event.key == pygame.K_r and completed_room_count == room_count:
                    if state == "dungeon" and is_in_trigger(player, "leave"):
                        # R in dungeon: back to hub
                        state = "hub"
                        active_gen = hub_gen
                            
                        # Load hub
                        spawn = hub_gen.load_complete(tile_size)
                            
                        # Preserve player money and respawn
                        current_money = player.money
                        player = Player(spawn[0], spawn[1])
                        player.money = current_money
                            
                        # Clear dungeon-specific state
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
                        return "menu"
                    elif quit_rect.collidepoint(event.pos):
                        return "quit"
                elif state == "dungeon":
                    # Shooting in dungeons
                    mouse_world = camera.screen_to_world(event.pos)
                    bullet = player.shoot(mouse_world)
                    if bullet:
                        bullets.append(bullet)

        # Update phase
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
            return  "dead" # Return to menu when player dies
                    
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
                progress_text += " - Press R to return to hub"
            text_surface = font.render(progress_text, True, (255, 255, 255))
            win.blit(text_surface, (20, 80))
            if is_in_trigger(player, "leave"):
                leave_text = "Press R to return to hub (when all rooms complete)"
                leave_surface = font.render(leave_text, True, (255, 255, 0))
                win.blit(leave_surface, (20, 100))
        elif state == "hub":         
            if is_in_trigger(player, "start"):
                start_text = "Press ENTER to start dungeon"
                start_surface = font.render(start_text, True, (0, 255, 0))
                win.blit(start_surface, (20, 100))
            elif is_in_trigger(player, "info"):
                info_text = "Press [PLACEHOLDER] for the Information Shelf"
                info_surface = font.render(info_text, True, (0, 255, 255))
                win.blit(info_surface, (20, 100))
            elif is_in_trigger(player, "quit"):
                quit_text = "Press ESC to quit to menu"
                quit_surface = font.render(quit_text, True, (255, 255, 0))
                win.blit(quit_surface, (20, 100))
            elif is_in_trigger(player, "shop"):
                quit_text = "Press [PLACEHOLDER] to shop"
                quit_surface = font.render(quit_text, True, (255, 255, 0))
                win.blit(quit_surface, (20, 100))
        
        # Draw inventory overlay if active
        if inventory_state:
            inventory_ui.draw(win, player.money)

                # Draw pause menu on top of everything, initialise rects every frame
        if paused:
            resume_rect, menu_rect, quit_rect = draw_pause_menu(win, screen_width, screen_height)
        else:
            resume_rect = menu_rect = quit_rect = pygame.Rect(0, 0, 0, 0)
            
        pygame.display.flip()
        await asyncio.sleep(0)

