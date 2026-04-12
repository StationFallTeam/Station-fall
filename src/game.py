import asyncio
import pygame
import sys

from src.background import SpaceBackground
from src.camera import Camera
from src.player import Player
from src.render import draw_objects, draw_pause_menu, draw_shop
from src.collision import handle_all_collisions, is_in_trigger
from src.inventory_ui import InventoryUI  
from dungeongen.classes import DungeonContext, CombatRoom
from dungeongen.rendering import draw_minimap
from dungeongen.loading import create_hub_generator, create_dungeon_generator

async def game(win, settings=None):
    if settings is None:
        settings = {'music_volume': 0.5, 'brightness': 1.0}
    
    music_volume = settings.get('music_volume', 0.5)
    brightness = settings.get('brightness', 1.0)
    
    VOLUME_STEP = 0.1
    BRIGHTNESS_STEP = 0.1
    screen_width, screen_height = 920, 920

    pygame.display.set_caption("Station Fall")
    clock = pygame.time.Clock()
    game_font = pygame.font.SysFont("Pixellari.ttf", 25)

    background = SpaceBackground(screen_width, screen_height)
    camera = Camera(screen_width, screen_height)
    bullets, coins, floating_texts = [], [], []
    inventory_ui = InventoryUI(screen_width, screen_height)

    # Initialize Tutorial system
    from src.tutorial import TutorialPopup, should_show_first_launch_tutorial
    tutorial_ui = TutorialPopup(screen_width, screen_height)
    
    # Auto-trigger only on the very first launch
    if should_show_first_launch_tutorial():
        tutorial_ui.show()
    
    inventory_state, paused, shop = False, False, False
    shop_items = [
        {"name": "Healing Kit", "price": 10, "image": pygame.image.load("sprites/shop/HealingKit.png")},
        {"name": "Blaster Upgrade", "price": 25, "image": pygame.image.load("sprites/shop/BlasterUpgrade.png")},
        {"name": "Space Suit Upgrade", "price": 15, "image": pygame.image.load("sprites/shop/SpaceSuitUpgrade.png")},
    ]

    hub_gen = create_hub_generator("hub")
    dungeon_gen = create_dungeon_generator()
    state, active_gen = "hub", hub_gen
    spawn = hub_gen.load_complete(40)
    player = Player(spawn[0], spawn[1])
    
    room_count, completed_room_count = 0, 0
    dungeon_context = DungeonContext(40)
    last_player_tile, tile_size = None, 40
    
    running = True
    while running:
        clock.tick(60)
        events = pygame.event.get() 

        # If Tutorial is visible, it intercepts the event list
        if tutorial_ui.visible:
            tutorial_ui.update(events)
        else:
            for event in events:
                if event.type == pygame.QUIT:
                    return "quit"
                elif event.type == pygame.KEYDOWN:
                    # KEYHANDLING: H for Help
                    if event.key == pygame.K_h:
                        tutorial_ui.show()
                    
                    elif event.key == pygame.K_ESCAPE:
                        if shop: shop = False
                        elif paused: paused = False
                        elif is_in_trigger(player, "quit"):
                            current_settings = {'music_volume': music_volume, 'brightness': brightness}
                            return "quit", current_settings
                        else: paused = not paused 
                    
                    # ... rest of your settings and movement keys ...
                    elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                        music_volume = min(music_volume + VOLUME_STEP, 1.0)
                        pygame.mixer.music.set_volume(music_volume)              
                    elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                        music_volume = max(music_volume - VOLUME_STEP, 0.0)
                        pygame.mixer.music.set_volume(music_volume)               
                    elif event.key == pygame.K_0: brightness = min(brightness + BRIGHTNESS_STEP, 1.0)        
                    elif event.key == pygame.K_9: brightness = max(brightness - BRIGHTNESS_STEP, 0.2)
                        
                    elif event.key == pygame.K_RETURN:
                        if state == "hub" and is_in_trigger(player, "start"):
                            state, active_gen = "dungeon", dungeon_gen
                            spawn, dungeon_context = dungeon_gen.load_complete(tile_size)
                            current_money = player.money
                            player = Player(spawn[0], spawn[1])
                            player.money = current_money
                            bullets.clear(); floating_texts.clear(); last_player_tile = None
                            room_count, completed_room_count = dungeon_gen.get_room_counts()

                    elif event.key == pygame.K_r and completed_room_count == room_count:
                        if state == "dungeon" and is_in_trigger(player, "leave"):
                            state, active_gen = "hub", hub_gen
                            spawn = hub_gen.load_complete(tile_size)
                            current_money = player.money
                            player = Player(spawn[0], spawn[1])
                            player.money = current_money
                            dungeon_context = DungeonContext(tile_size)
                            bullets.clear(); floating_texts.clear(); last_player_tile = None
                            room_count, completed_room_count = 0, 0

                    elif event.key == pygame.K_i: inventory_state = not inventory_state
                    elif event.key == pygame.K_e and is_in_trigger(player, "shop"): shop = not shop

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # ... [Your mouse handling code for shop/shooting] ...
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
                        if bullet: bullets.append(bullet)

        # Physics and Update logic (Blocked if tutorial/pause/shop is open)
        if not paused and not shop and not tutorial_ui.visible:
            keys = pygame.key.get_pressed()
            player.update(keys); camera.update(player)
            # ... handle collisions and enemies ...
            floating_texts = [ft for ft in floating_texts if ft.update()]
        
            if state == "dungeon" and active_gen.rooms:
                player_tile_x, player_tile_y = int(player.x // tile_size), int(player.y // tile_size)
                current_player_tile = (player_tile_x, player_tile_y)
                
                if current_player_tile != last_player_tile:
                    last_player_tile = current_player_tile
                    for room in active_gen.rooms:
                        if (room.triggerRect.x <= player_tile_x < room.triggerRect.x + room.triggerRect.w and
                            room.triggerRect.y <= player_tile_y < room.triggerRect.y + room.triggerRect.h):
                            if isinstance(room, CombatRoom): room.on_enter(dungeon_context)
                            break
                
                for room in active_gen.rooms:
                    if isinstance(room, CombatRoom): room.update(dungeon_context)
                
                room_count, completed_room_count = active_gen.get_room_counts()
                for enemy in dungeon_context.enemies[:]:
                    enemy.update(player.rect)
                    if hasattr(enemy, 'pop_projectiles'): bullets.extend(enemy.pop_projectiles())
                        
            for bullet in bullets[:]:
                bullet.update()
                if bullet.is_dead(): bullets.remove(bullet)
            
            enemies_list = dungeon_context.enemies if state == "dungeon" else []
            handle_all_collisions(player, enemies_list, bullets, floating_texts, coins)
            
            if player.health <= 0: return "dead", {'music_volume': music_volume, 'brightness': brightness}
                        
            for coin in coins[:]:
                coin.update()
                if player.rect.colliderect(coin.rect):
                    player.money += coin.value
                    coins.remove(coin)

        # Drawing Phase
        win.fill((0, 0, 0))
        draw_objects(win, player, dungeon_context.enemies if state == "dungeon" else [], bullets, camera, background, coins, floating_texts, active_gen, tile_size)
        draw_minimap(win, active_gen.tiles, player.rect.centerx, player.rect.centery, tile_size, spawn[0], spawn[1], 160, 160)
        
        if inventory_state: inventory_ui.draw(win, player.money)
        if paused: resume_rect, menu_rect, quit_rect = draw_pause_menu(win, screen_width, screen_height)
        if shop: item_rects = draw_shop(win, screen_width, screen_height, player.money, shop_items)

        # Draw Tutorial on top
        if tutorial_ui.visible:
            tutorial_ui.draw(win)

        if brightness < 1.0:
            dark_surface = pygame.Surface((screen_width, screen_height)); dark_surface.set_alpha(int((1.0 - brightness) * 255)); dark_surface.fill((0, 0, 0)); win.blit(dark_surface, (0, 0))

        pygame.display.flip()
        await asyncio.sleep(0)