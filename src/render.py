import pygame

def draw_objects(win, player, enemies, camera):
    # 1. Draw Player (Shifted by camera)
    player_screen_rect = camera.apply(player)
    current_frame = player.animations[player.direction][int(player.frameIndex)]
    win.blit(current_frame, player_screen_rect)

    # 2. Draw Enemies (Shifted by camera)
    for enemy in enemies:
        enemy_screen_rect = camera.apply(enemy.rect)
        pygame.draw.rect(win, enemy.color, enemy_screen_rect)