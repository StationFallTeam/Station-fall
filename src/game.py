import asyncio
import sys
import pygame

# Custom game imports
from src.background import SpaceBackground
from src.camera import Camera
from src.player import Player
from src.render import draw_objects, draw_pause_menu, draw_shop
from src.collision import handle_all_collisions, is_in_trigger
from src.inventory_ui import InventoryUI  
from src.floating_texts import FloatingText
from src.health_drop import HealthDrop
from src.tutorial import TutorialPopup
from src.assets import resolve_asset_path

# Dungeon generation imports
from dungeongen.classes import DungeonContext, CombatRoom
from dungeongen.rendering import draw_minimap
from dungeongen.loading import (
    create_hub_generator,
    create_dungeon_generator
)

async def game(win, settings=None):
    # --- Initialization ---
    if settings is None:
        settings = {'music_volume': 0.5, 'brightness': 1.0}
    
    music_volume = settings.get('music_volume', 0.5)
    brightness = settings.get('brightness', 1.0)

    # change music to standard background
    pygame.mixer.music.stop()
    pygame.mixer.music.load('sound/peace-in-void.ogg')
    pygame.mixer.music.set_volume(music_volume)
    pygame.mixer.music.play(-1)
    
    VOLUME_STEP = 0.1
    BRIGHTNESS_STEP = 0.1
    screen_width, screen_height = 920, 920

    pygame.display.set_caption("Station Fall")
    clock = pygame.time.Clock()
    game_font = pygame.font.SysFont("Pixellari.ttf", 25)

    # Core Systems
    background = SpaceBackground(screen_width, screen_height)
    camera = Camera(screen_width, screen_height)
    inventory_ui = InventoryUI(screen_width, screen_height)
    tutorial_popup = TutorialPopup(screen_width, screen_height)
    
<<<<<<< HEAD
    # Entity Lists
    bullets, coins, floating_texts = [], [], []
    
    # Game UI States
    inventory_state = False  
    paused = False 
    shop = False 
    
    # Shop Setup
=======
    # Game state
    inventory_state = False  # For inventory overlay
    paused = False # for pause menu - Wil
    minimap_fullscreen = False

    shop = False # for the shop
>>>>>>> origin/main
    shop_items = [
        {"name": "Healing Kit",         "price": 10,  "image": pygame.image.load(resolve_asset_path("sprites/shop/HealingKit.png"))},
        {"name": "Blaster Upgrade",     "price": 25,  "image": pygame.image.load(resolve_asset_path("sprites/shop/BlasterUpgrade.png"))},
        {"name": "Space Suit Upgrade",  "price": 15,  "image": pygame.image.load(resolve_asset_path("sprites/shop/SpaceSuitUpgrade.png"))},
    ]

    # Map Generation
    tile_size = 40
    hub_gen = create_hub_generator("hub")
    dungeon_gen = create_dungeon_generator()
    
    state = "hub"
    active_gen = hub_gen
    spawn = hub_gen.load_complete(tile_size)
    
    # Entity Initialization
    player = Player(spawn[0], spawn[1])
    dungeon_context = DungeonContext(tile_size)
    
    last_player_tile = None
    room_count = 0
    completed_room_count = 0
    
    shoot_sound = pygame.mixer.Sound(resolve_asset_path("sound/shoot.ogg"))
    shoot_sound.set_volume(0.4)

    running = True
    while running:
        clock.tick(60)
        events = pygame.event.get()

        # 1. ANIMATION UPDATE (FIX: Called every frame outside event loop)
        # This allows the tutorial to fade in smoothly even if the mouse isn't moving.
        tutorial_popup.update(events)

        # 2. EVENT HANDLING
        for event in events:
            if event.type == pygame.QUIT:
                return "quit"

            # 3. INPUT BLOCKING
            # If tutorial is open, we skip the rest of the game input logic
            if tutorial_popup.visible:
                continue

            # Keyboard Input
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if shop: shop = False
                    elif paused: paused = False
                    elif is_in_trigger(player, "quit"):
<<<<<<< HEAD
                        pygame.quit()
                        sys.exit()
                    else: paused = not paused 
=======
                        # Return current settings when quitting
                        current_settings = {'music_volume': music_volume, 'brightness': brightness}
                        return "quit", current_settings
                    else:
                        paused = not paused 
>>>>>>> origin/main
                
                # Settings
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
<<<<<<< HEAD
                
                # Tutorial Trigger (H Key)
=======
                        
                elif event.key == pygame.K_RETURN:
                    if state == "hub" and is_in_trigger(player, "start"):
                        coins.clear()
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
                elif event.key == pygame.K_m:
                    minimap_fullscreen = not minimap_fullscreen
                elif event.key == pygame.K_e: # Shop
                    if is_in_trigger(player, "shop"):
                        shop = not shop
>>>>>>> origin/main
                elif event.key == pygame.K_h:
                    if state == "hub" and is_in_trigger(player, "info"):
                        tutorial_popup.show()
                        
                # Dungeon Transitions
                elif event.key == pygame.K_RETURN:
                    if state == "hub" and is_in_trigger(player, "start"):
                        state = "dungeon"
                        active_gen = dungeon_gen
                        spawn, dungeon_context = dungeon_gen.load_complete(tile_size)
                        player.x, player.y = spawn[0], spawn[1]
                        bullets.clear()
                        floating_texts.clear()
                        room_count, completed_room_count = dungeon_gen.get_room_counts()
                
                elif event.key == pygame.K_r and completed_room_count == room_count:
                    if state == "dungeon" and is_in_trigger(player, "leave"):
                        state = "hub"
                        active_gen = hub_gen
                        spawn = hub_gen.load_complete(tile_size)
                        player.x, player.y = spawn[0], spawn[1]
                        dungeon_context = DungeonContext(tile_size)
                        bullets.clear()

                elif event.key == pygame.K_i:
                    inventory_state = not inventory_state
                elif event.key == pygame.K_e:
                    if is_in_trigger(player, "shop"):
                        shop = not shop

            # Mouse Input
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if shop:
                    for idx, rect in enumerate(item_rects):
                        item = shop_items[idx]
                        if rect.collidepoint(event.pos) and player.money >= item['price']:
                            player.money -= item['price']
                            if item['name'] == "Healing Kit": player.health = min(player.max_health, player.health + 20)
                            elif item['name'] == "Blaster Upgrade": player.damage += 5
                            elif item['name'] == "Space Suit Upgrade":
                                player.max_health += 10
                                player.health = min(player.health, player.max_health)       
                elif paused:
                    if resume_rect.collidepoint(event.pos): paused = False
                    elif menu_rect.collidepoint(event.pos): return "menu", {'music_volume': music_volume, 'brightness': brightness}
                    elif quit_rect.collidepoint(event.pos): return "quit", {'music_volume': music_volume, 'brightness': brightness}
                elif state == "dungeon":
                    mouse_world = camera.screen_to_world(event.pos)
                    bullet = player.shoot(mouse_world)
<<<<<<< HEAD
                    if bullet: bullets.append(bullet)
=======
                    if bullet:
                        shoot_sound.play()
                        bullets.append(bullet)
>>>>>>> origin/main

        # 4. PHYSICS / LOGIC UPDATE PHASE
        if not paused and not shop and not tutorial_popup.visible:
            keys = pygame.key.get_pressed()
            player.update(keys)
            camera.update(player)
            floating_texts = [ft for ft in floating_texts if ft.update()]
        
            if state == "dungeon" and active_gen.rooms:
                player_tile = (int(player.x // tile_size), int(player.y // tile_size))
                if player_tile != last_player_tile:
                    last_player_tile = player_tile
                    for room in active_gen.rooms:
                        if (room.triggerRect.x <= player_tile[0] < room.triggerRect.x + room.triggerRect.w and
                            room.triggerRect.y <= player_tile[1] < room.triggerRect.y + room.triggerRect.h):
                            if isinstance(room, CombatRoom): room.on_enter(dungeon_context)
                
                for room in active_gen.rooms:
                    if isinstance(room, CombatRoom): room.update(dungeon_context)
                room_count, completed_room_count = active_gen.get_room_counts()
                    
                for enemy in dungeon_context.enemies:
                    enemy.update(player.rect)
                    if hasattr(enemy, 'pop_projectiles'): bullets.extend(enemy.pop_projectiles())
                        
            for bullet in bullets[:]:
                bullet.update()
                if bullet.is_dead(): bullets.remove(bullet)
            
            enemies_list = dungeon_context.enemies if state == "dungeon" else []
            handle_all_collisions(player, enemies_list, bullets, floating_texts, coins)
            
            if player.health <= 0:
                return "dead", {'music_volume': music_volume, 'brightness': brightness}
                        
            for coin in coins[:]:
                coin.update()
                if player.rect.colliderect(coin.rect):
                    if isinstance(coin, HealthDrop):
                        player.health = min(player.health + coin.heal_amount, player.max_health)
                    else:
                        player.money += coin.value
                    coins.remove(coin)

        # 5. DRAWING PHASE
        win.fill((0, 0, 0))
        
        # World Objects
        enemy_list = dungeon_context.enemies if state == "dungeon" else []
        draw_objects(win, player, enemy_list, bullets, camera, background, coins, floating_texts, active_gen, tile_size)
        
<<<<<<< HEAD
        # UI Elements
        draw_minimap(win, active_gen.tiles, player.rect.centerx, player.rect.centery, tile_size, spawn[0], spawn[1], 160, 160)

        # Text UI
=======
        if state == "dungeon":
            minimap_width = screen_width - 24 if minimap_fullscreen else 160
            minimap_height = screen_height - 24 if minimap_fullscreen else 160
            minimap_padding = 12

            draw_minimap(
                win,
                active_gen.tiles,
                player.rect.centerx,
                player.rect.centery,
                tile_size,
                minimap_width=minimap_width,
                minimap_height=minimap_height,
                padding=minimap_padding,
                view_radius_tiles=22 if minimap_fullscreen else 16,
                rooms=active_gen.rooms,
                hallways=active_gen.hallways,
                full_map=minimap_fullscreen,
            )
        # Some text tips
>>>>>>> origin/main
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
                info_text = "Press H to read the help logs"
                info_surface = game_font.render(info_text, True, (0, 255, 255))
                win.blit(info_surface, (20, 80))
            elif is_in_trigger(player, "quit"):
                quit_text = "Press ESC to quit to menu"
                quit_surface = game_font.render(quit_text, True, (255, 255, 0))
                win.blit(quit_surface, (20, 80))
            elif is_in_trigger(player, "shop"):
                shop_text = "Press E to browse the shop"
                shop_surface = game_font.render(shop_text, True, (255, 255, 0))
                win.blit(shop_surface, (20, 80))
<<<<<<< HEAD
=======
        
        # Draw inventory overlay if active
        if inventory_state:
            inventory_ui.draw(win, player.money, visible=inventory_state)
>>>>>>> origin/main

        if inventory_state: inventory_ui.draw(win, player.money)
        if paused: resume_rect, menu_rect, quit_rect = draw_pause_menu(win, screen_width, screen_height)
        if shop: item_rects = draw_shop(win, screen_width, screen_height, player.money, shop_items)

        # 6. DRAW TUTORIAL LAST (So it covers the world)
        tutorial_popup.draw(win)
                    
        # Apply Brightness
        if brightness < 1.0:
            dark = pygame.Surface((screen_width, screen_height))
            dark.set_alpha(int((1.0 - brightness) * 255))
            dark.fill((0, 0, 0))
            win.blit(dark, (0, 0))

        pygame.display.flip()
        await asyncio.sleep(0)