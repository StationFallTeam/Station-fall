import asyncio
import sys
import pygame

# --- IMPORT CUSTOM MODULES ---
from src.background import SpaceBackground
from src.camera import Camera
from src.player import Player
from src.render import draw_objects, draw_pause_menu, draw_shop
from src.collision import handle_all_collisions, is_in_trigger
from src.inventory_ui import InventoryUI  
from src.floating_texts import FloatingText
from src.health_drop import HealthDrop
from src.tutorial import TutorialPopup

# --- IMPORT DUNGEON GENERATION MODULES ---
from dungeongen.classes import DungeonContext, CombatRoom
from dungeongen.rendering import draw_minimap
from dungeongen.loading import (
    create_hub_generator,
    create_dungeon_generator
)

async def game(win, settings=None):
    """
    Main Game Function: Handles the core loop for both the Hub and the Dungeon.
    """
    # 1. INITIALIZE SETTINGS & CONSTANTS
    if settings is None:
        settings = {'music_volume': 0.5, 'brightness': 1.0}
    
    music_volume = settings.get('music_volume', 0.5)
    brightness = settings.get('brightness', 1.0)
    
    screen_width, screen_height = 920, 920
    tile_size = 40

    pygame.display.set_caption("Station Fall")
    clock = pygame.time.Clock()
    game_font = pygame.font.SysFont("Pixellari.ttf", 25)

    # 2. INITIALIZE GAME OBJECTS
    background = SpaceBackground(screen_width, screen_height)
    camera = Camera(screen_width, screen_height)
    inventory_ui = InventoryUI(screen_width, screen_height)
    tutorial_popup = TutorialPopup(screen_width, screen_height)
    
    bullets = []
    coins = []
    floating_texts = []
    
    # 3. SETUP UI & GAME STATES
    inventory_state = False  # Is inventory open?
    paused = False           # Is pause menu open?
    shop = False             # Is shop open?
    
    # Define items available in the shop terminal
    shop_items = [
        {"name": "Healing Kit", "price": 10, "image": pygame.image.load("sprites/shop/HealingKit.png")},
        {"name": "Blaster Upgrade", "price": 25, "image": pygame.image.load("sprites/shop/BlasterUpgrade.png")},
        {"name": "Space Suit Upgrade", "price": 15, "image": pygame.image.load("sprites/shop/SpaceSuitUpgrade.png")},
    ]

    # 4. LOAD WORLD GENERATORS
    hub_gen = create_hub_generator("hub")
    dungeon_gen = create_dungeon_generator()
    
    # Start in the Hub
    state = "hub"
    active_gen = hub_gen
    spawn = hub_gen.load_complete(tile_size)
    
    player = Player(spawn[0], spawn[1])
    dungeon_context = DungeonContext(tile_size)
    
    last_player_tile = None
    room_count = 0
    completed_room_count = 0
    
    # --- CORE GAME LOOP ---
    running = True
    while running:
        clock.tick(60) # Lock to 60 FPS
        events = pygame.event.get()

        # UPDATING TUTORIAL ANIMATIONS
        # This must be called EVERY frame so that fade-in/slide-in works even 
        # when the mouse isn't moving.
        tutorial_popup.update(events)

        # EVENT HANDLING (Input Processing)
        for event in events:
            if event.type == pygame.QUIT:
                return "quit"

            # INPUT LOCK: If the tutorial is visible, skip all other game inputs
            if tutorial_popup.visible:
                continue

            if event.type == pygame.KEYDOWN:
                # Handle Menus
                if event.key == pygame.K_ESCAPE:
                    if shop: shop = False
                    elif paused: paused = False
                    elif is_in_trigger(player, "quit"):
                        pygame.quit()
                        sys.exit()
                    else: paused = not paused 
                
                # Help/Tutorial key
                elif event.key == pygame.K_h:
                    if state == "hub" and is_in_trigger(player, "info"):
                        tutorial_popup.show()
                
                # UI Toggles
                elif event.key == pygame.K_i: inventory_state = not inventory_state
                elif event.key == pygame.K_e:
                    if is_in_trigger(player, "shop"): shop = not shop

                # Dungeon Transitions
                elif event.key == pygame.K_RETURN:
                    if state == "hub" and is_in_trigger(player, "start"):
                        state = "dungeon"
                        active_gen = dungeon_gen
                        spawn, dungeon_context = dungeon_gen.load_complete(tile_size)
                        # Carry over money to new player instance
                        current_money = player.money
                        player = Player(spawn[0], spawn[1])
                        player.money = current_money
                        bullets.clear()
                        floating_texts.clear()
                        room_count, completed_room_count = dungeon_gen.get_room_counts()

                elif event.key == pygame.K_r and completed_room_count == room_count:
                    if state == "dungeon" and is_in_trigger(player, "leave"):
                        state = "hub"
                        active_gen = hub_gen
                        spawn = hub_gen.load_complete(tile_size)
                        current_money = player.money
                        player = Player(spawn[0], spawn[1])
                        player.money = current_money
                        dungeon_context = DungeonContext(tile_size)
                        bullets.clear()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Shop Interaction Logic
                if shop:
                    for idx, rect in enumerate(item_rects):
                        item = shop_items[idx]
                        if rect.collidepoint(event.pos) and player.money >= item['price']:
                            player.money -= item['price']
                            if item['name'] == "Healing Kit": player.health = min(player.max_health, player.health + 20)
                            elif item['name'] == "Blaster Upgrade": player.damage += 5
                            elif item['name'] == "Space Suit Upgrade": player.max_health += 10
                
                # Pause Menu Interaction
                elif paused:
                    if resume_rect.collidepoint(event.pos): paused = False
                    elif menu_rect.collidepoint(event.pos): return "menu", {'music_volume': music_volume, 'brightness': brightness}
                    elif quit_rect.collidepoint(event.pos): return "quit", {'music_volume': music_volume, 'brightness': brightness}
                
                # Combat Shooting
                elif state == "dungeon":
                    mouse_world = camera.screen_to_world(event.pos)
                    bullet = player.shoot(mouse_world)
                    if bullet: bullets.append(bullet)

        # WORLD UPDATE PHASE
        # Game logic (movement/enemies/collisions) only runs when UI is closed
        if not paused and not shop and not tutorial_popup.visible:
            keys = pygame.key.get_pressed()
            player.update(keys)
            camera.update(player)
            floating_texts = [ft for ft in floating_texts if ft.update()]

            # Dungeon Logic & Enemy Spawning
            if state == "dungeon" and active_gen.rooms:
                player_tile = (int(player.x // tile_size), int(player.y // tile_size))
                # Check if player entered a new room trigger
                if player_tile != last_player_tile:
                    last_player_tile = player_tile
                    for room in active_gen.rooms:
                        if (room.triggerRect.x <= player_tile[0] < room.triggerRect.x + room.triggerRect.w and
                            room.triggerRect.y <= player_tile[1] < room.triggerRect.y + room.triggerRect.h):
                            if isinstance(room, CombatRoom): room.on_enter(dungeon_context)
                
                # Update combat room status
                for room in active_gen.rooms:
                    if isinstance(room, CombatRoom): room.update(dungeon_context)
                
                room_count, completed_room_count = active_gen.get_room_counts()
                
                # Update Enemy AI
                for enemy in dungeon_context.enemies:
                    enemy.update(player.rect)
                    if hasattr(enemy, 'pop_projectiles'): bullets.extend(enemy.pop_projectiles())

            # Update Projectiles
            for bullet in bullets[:]:
                bullet.update()
                if bullet.is_dead(): bullets.remove(bullet)
            
            # COLLISION SYSTEM
            enemies_list = dungeon_context.enemies if state == "dungeon" else []
            handle_all_collisions(player, enemies_list, bullets, floating_texts, coins)
            
            # Check Death State
            if player.health <= 0:
                return "dead", {'music_volume': music_volume, 'brightness': brightness}
                        
            # Collect Coins/Items
            for coin in coins[:]:
                coin.update()
                if player.rect.colliderect(coin.rect):
                    if isinstance(coin, HealthDrop):
                        player.health = min(player.health + coin.heal_amount, player.max_health)
                    else:
                        player.money += coin.value
                    coins.remove(coin)

        # DRAW PHASE
        win.fill((0, 0, 0))
        
        # 1. Draw Game World (Relative to Camera)
        enemy_list = dungeon_context.enemies if state == "dungeon" else []
        draw_objects(win, player, enemy_list, bullets, camera, background, coins, floating_texts, active_gen, tile_size)
        
        # 2. Draw Minimap
        draw_minimap(win, active_gen.tiles, player.rect.centerx, player.rect.centery, tile_size, spawn[0], spawn[1], 160, 160)

        # 3. Draw Contextual Text Tips
        if state == "dungeon":
            txt = f"Rooms: {completed_room_count}/{room_count}"
            win.blit(game_font.render(txt, True, (255,255,255)), (20, 80))
        elif state == "hub":
            if is_in_trigger(player, "info"):
                win.blit(game_font.render("Press H to read the help logs", True, (0, 255, 255)), (20, 80))

        # 4. Draw UI Overlays (Always on top of world)
        if inventory_state: inventory_ui.draw(win, player.money)
        if paused: resume_rect, menu_rect, quit_rect = draw_pause_menu(win, screen_width, screen_height)
        if shop: item_rects = draw_shop(win, screen_width, screen_height, player.money, shop_items)

        # 5. Draw Tutorial (Must be drawn last to be the top-most layer)
        tutorial_popup.draw(win)
                    
        # 6. Apply Screen Brightness (Final Filter)
        if brightness < 1.0:
            dark = pygame.Surface((screen_width, screen_height))
            dark.set_alpha(int((1.0 - brightness) * 255))
            dark.fill((0, 0, 0))
            win.blit(dark, (0, 0))

        pygame.display.flip()
        await asyncio.sleep(0) # Keep async loop responsive for web/pygbag