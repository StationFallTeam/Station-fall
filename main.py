import pygame
from enemy import Enemy
pygame.init()
pygame.mixer.init()

# Set up display
screen_width = 500
screen_height = 500
win = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("WASD Movement Test")

# Player variables
x = 100
y = 100
width = 80 
height = 120
vel = 5 # Velocity or speed of movement

player_img = pygame.image.load("IMG_5427.jpg").convert_alpha()
player_img = pygame.transform.scale(player_img, (width, height))

enemy = Enemy(300, 300)#loading one enemy 


run = True
while run:
    # Set frame rate
    pygame.time.delay(10) # Reduced delay for smoother movement

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    # Get the state of all keyboard keys
    keys = pygame.key.get_pressed()

    # Movement logic: update x and y coordinates based on key states
    if keys[pygame.K_a]:
        x -= vel
    if keys[pygame.K_d]:
        x += vel
    if keys[pygame.K_w]:
        y -= vel # subtracting from y moves up (top-left is 0,0)
    if keys[pygame.K_s]:
        y += vel #  moves down

    player_rect = pygame.Rect(x, y, width, height)#so the enemy knows where the player is


    # Optional: Keep player within screen boundaries
    x = max(0, min(x, screen_width - width))
    y = max(0, min(y, screen_height - height))

    enemy.update(player_rect) # Update enemy position based on player position

    # Drawing
    win.fill((0, 0, 0)) # Fill the background with black to clear previous frames
    win.blit(player_img, (x, y))
    enemy.draw(win) # Draw the enemy
    pygame.display.update() # Update the display

pygame.quit()
