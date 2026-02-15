import pygame

def draw_objects(win, player, enemies, camera):
    # 1. Get the current animation frame
    current_frame = player.animations[player.direction][int(player.frameIndex)]
    
    # 2. Get the player's position relative to the camera
    player_screen_pos = camera.apply(player.get_rect())
    
    # 3. Draw the player
    win.blit(current_frame, player_screen_pos)

    # 4. Draw enemies relative to camera
    for enemy in enemies:
        enemy_screen_pos = camera.apply(enemy.rect)
        pygame.draw.rect(win, enemy.color, enemy_screen_pos)