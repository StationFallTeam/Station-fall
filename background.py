import pygame
import random

# --- Configuration ---
WIDTH, HEIGHT = 800, 600
FPS = 60
TILE_SIZE = 64  # Size of floor tiles
PLAYER_SPEED = 5

# Colors
COLOR_BG = (10, 10, 15)      # Deep space
COLOR_TILE = (30, 30, 35)    # Station floor
COLOR_GRID = (45, 45, 50)    # Floor panel edges
COLOR_PLAYER = (0, 200, 255) # Scavenger blue

class Background:
    def __init__(self, image_path):
        # 1. Load the PNG
        try:
            self.tile_image = pygame.image.load(image_path).convert_alpha()
        except pygame.error:
            # Fallback if image fails to load
            print(f"Warning: Could not load {image_path}. Using placeholder.")
            self.tile_image = pygame.Surface((TILE_SIZE, TILE_SIZE))
            self.tile_image.fill((50, 50, 50))

        # Get the actual dimensions of your PNG (in case it isn't exactly TILE_SIZE)
        self.img_w = self.tile_image.get_width()
        self.img_h = self.tile_image.get_height()

        # Distant stars (same as before)
        self.stars = [(random.randint(0, WIDTH), random.randint(0, HEIGHT)) for _ in range(50)]

    def draw(self, screen, cam_x, cam_y):
        # Draw Parallax Stars
        for star in self.stars:
            sx = (star[0] - cam_x * 0.1) % WIDTH
            sy = (star[1] - cam_y * 0.1) % HEIGHT
            pygame.draw.circle(screen, (200, 200, 200), (int(sx), int(sy)), 1)

        # Draw PNG Tiles
        # We use modulo on the image width/height for seamless wrapping
        start_x = -(cam_x % self.img_w)
        start_y = -(cam_y % self.img_h)

        # Loop from the start offset across the screen width/height
        for x in range(int(start_x), WIDTH + self.img_w, self.img_w):
            for y in range(int(start_y), HEIGHT + self.img_h, self.img_h):
                screen.blit(self.tile_image, (x, y))
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Station Fall: Early Prototype")
    clock = pygame.time.Clock()

    bg = Background(Background.png)
    
    # Player's position in the WORLD (not the screen)
    player_world_x = 0
    player_world_y = 0

    running = True
    while running:
        # 1. Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # 2. Movement Logic
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w] or keys[pygame.K_UP]:    player_world_y -= PLAYER_SPEED
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:  player_world_y += PLAYER_SPEED
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:  player_world_x -= PLAYER_SPEED
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: player_world_x += PLAYER_SPEED

        # 3. Rendering
        screen.fill(COLOR_BG)

        # The camera follows the player. 
        # By passing player_world_x/y to the bg, we tell it how much to shift.
        bg.draw(screen, player_world_x, player_world_y)

        # Draw the Player in the center of the screen
        # Since the background moves, the player can stay at (WIDTH/2, HEIGHT/2)
        pygame.draw.rect(screen, COLOR_PLAYER, (WIDTH//2 - 16, HEIGHT//2 - 16, 32, 32))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()