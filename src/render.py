import pygame

def draw_objects(win, player, enemies, camera):
    # 1. Get the current animation frame from the player
    current_frame = player.animations[player.direction][int(player.frameIndex)]
    
    # 2. Adjust the player's world position to screen position
    player_screen_rect = camera.apply(player.get_rect())
    
    # 3. Draw the player at the camera-adjusted position
    win.blit(current_frame, player_screen_rect)

    # 4. Draw enemies at their camera-adjusted positions
    for enemy in enemies:
        enemy_screen_rect = camera.apply(enemy.rect)
        pygame.draw.rect(win, enemy.color, enemy_screen_rect)