import pygame
pygame.init()
pygame.mixer.init()

# Set up display
screen_width = 500
screen_height = 500
win = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("WASD Movement Test")

clock = pygame.time.Clock()

# Player variables
x = 100
y = 100
width = 48
height = 48
vel = 5 # Velocity or speed of movement

spriteSheet = pygame.image.load("player_sheet.png").convert_alpha()

def getFrame(sheet, x, y, width, height):
    frame = pygame.Surface((width, height), pygame.SRCALPHA)
    frame.blit(sheet, (0,0), (x, y, width, height))
    return frame


# Animations (4 directions)
animations = {
    "down": [],
    "left": [],
    "right": [],
    "up": []
}

directions = ["down", "left", "right", "up"]

for row in range(4): # 4 rows
    for col in range(4): # 4 frames per row
        frame = getFrame(spriteSheet, col * width, row * height, width, height)
        animations[directions[row]].append(frame)

direction = "down"
frameIndex = 0
animationSpeed = 0.2
moving = False

run = True
while run:
    clock.tick(60)
    moving = False

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    # Get the state of all keyboard keys
    keys = pygame.key.get_pressed()

    # Movement logic: update x and y coordinates based on key states
    if keys[pygame.K_a]:
        x -= vel
        direction = "left"        
        moving = True
    if keys[pygame.K_d]:
        direction = "right"
        x += vel
        moving = True
    if keys[pygame.K_w]:
        y -= vel # subtracting from y moves up (top-left is 0,0)
        direction = "up"        
        moving = True
    if keys[pygame.K_s]:
        y += vel #  moves down
        direction = "down"
        moving = True

    # Optional: Keep player within screen boundaries
    x = max(0, min(x, screen_width - width))
    y = max(0, min(y, screen_height - height))

    if moving:
        frameIndex += animationSpeed
        if frameIndex >= len(animations[direction]):
            frameIndex = 0
    else:
        frameIndex = 0

    # Drawing
    win.fill((0, 0, 0)) # Fill the background with black to clear previous frames
    win.blit(animations[direction][int(frameIndex)], (x, y))
    pygame.display.update() # Update the display

pygame.quit()
