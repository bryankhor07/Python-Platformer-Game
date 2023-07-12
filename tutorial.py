import os
import random
import math
import pygame
# I'm doing all this OS stuff is because we are going to be dynamically loading all of the sprite sheets
# and the images so we don't have to manually like type out the file names that we want
from os import listdir
from os.path import isfile, join
pygame.init() # We need to initialize the py game module.

pygame.display.set_caption("Platformer Game") # This is setting the caption at the top of the window

WIDTH, HEIGHT = 1000, 700 # Width and height of our screen.
FPS = 60
PLAYER_VEL = 5 # This is going to be the speed at which my player moves around the screen.

window = pygame.display.set_mode((WIDTH, HEIGHT)) # This is going to create the PI game window for us.

# This function is used to flip our player when it moves left or right.
def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]


def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            # We don't need to flip the player when it moves right because the original image 
            # faces the right direction
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            # We need to flip the player when it moves left. 
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites) 
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites


def get_block(size):
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    # Change the second argument to load different terrain blocks.
    # First option: 0 
    # Second option: 64
    # Third option: 128
    rect = pygame.Rect(96, 0, size, size)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)


class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 1 # Increment the gravity if you want gravity to be faster.
    SPRITES = load_sprite_sheets("MainCharacters", "NinjaFrog", 32, 32, True) # Change your character by editing the second parameter
    ANIMATION_DELAY = 3 # Decrement this number for faster animation and increment for slower animation

    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        # The x and y velocity is going to denote what we call it 
        # here, how fast we are moving our player. Every single frame in both directions.
        self.x_vel = 0 
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0

    def jump(self):
        self.y_vel = -self.GRAVITY * 8 # Change the number to change the speed of your jump.
        self.animation_count = 0
        self.jump_count += 1
        # Double Jump implementation
        if self.jump_count == 1:
            self.fall_count = 0

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def make_hit(self):
        self.hit = True

    def move_left(self, vel):
        # Now the reason we use negative velocity here is because if we want to go left, 
        # we have to subtract from our exposition in PI game.
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self, fps):
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)

        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2:
            self.hit = False
            self.hit_count = 0

        self.fall_count += 1
        self.update_sprite()

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def hit_head(self):
        self.count = 0
        self.y_vel *= -1

    def update_sprite(self):
        sprite_sheet = "idle"
        if self.hit:
            sprite_sheet = "hit"
        elif self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    # What we need to do here is essentially update the rectangle that bounds our character based on the sprite that we're showing.
    def update(self):
        # Now pretty much what's going to happen here is depending on what Sprite we have.
        # If it's slightly smaller, slightly bigger, whatever, 
        # we're going to constantly adjust the rectangle, specifically we're going to adjust the width and the height of it,
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self, win, offset_x):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))

# This will be a base class that we use for essentially all of our objects,
# just so that the collision will be uniform across all of them.
class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))


class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)


class Fire(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")
        self.fire = load_sprite_sheets("Traps", "Fire", width, height)
        self.image = self.fire["off"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def loop(self):
        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0

# This function is used to get the background color of the game.
def get_background(name): # The name variable is going to be the color of our background.
    image = pygame.image.load(join("assets", "Background", name))
    _, _, width, height = image.get_rect()
    tiles = []

    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles, image


def draw(window, background, bg_image, player, objects, offset_x):
    for tile in background:
        window.blit(bg_image, tile)

    for obj in objects:
        obj.draw(window, offset_x)

    player.draw(window, offset_x)

    pygame.display.update()


def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        # This is all you need to do to determine if two objects are colliding.
        if pygame.sprite.collide_mask(player, obj):
            if dy > 0:
                # This line of code ensures the feet of your player stays on top of the terrain.
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                # This line of code ensures the head of you player doesn't go into a block when jumping.
                player.rect.top = obj.rect.bottom
                player.hit_head()

            collided_objects.append(obj)

    return collided_objects


def collide(player, objects, dx):
    player.move(dx, 0)
    player.update()
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break

    player.move(-dx, 0)
    player.update()
    return collided_object

# What we're going to do is essentially check the keys that are being pressed on the keyboard. 
# If you're pressing left or you're pressing right,
# then we'll move the character to the left or to the right.
def handle_move(player, objects):
    keys = pygame.key.get_pressed()

    player.x_vel = 0
    collide_left = collide(player, objects, -PLAYER_VEL * 2)
    collide_right = collide(player, objects, PLAYER_VEL * 2)

    if keys[pygame.K_LEFT] and not collide_left: # K_LEFT is the left arrow key
        player.move_left(PLAYER_VEL) # Move left when user press left arrow key
    if keys[pygame.K_RIGHT] and not collide_right: # K_RIGHT is the right arrow key
        player.move_right(PLAYER_VEL) # Move right when user press right arrow key

    vertical_collide = handle_vertical_collision(player, objects, player.y_vel)
    to_check = [collide_left, collide_right, *vertical_collide]

    for obj in to_check:
        if obj and obj.name == "fire":
            player.make_hit()


def main(window):
    clock = pygame.time.Clock()
    background, bg_image = get_background("Purple.png") # Change background color here

    block_size = 96

    player = Player(100, 100, 50, 50) # Modify player width and height here
    fire = Fire(895, HEIGHT - block_size - 64, 16, 32) # Change the first argument to change the position of fire on the x-axis.
    fire2 = Fire(1280, HEIGHT - block_size - 64, 16, 32)
    fire3 = Fire(1665, HEIGHT - block_size - 64, 16, 32)
    fire4 = Fire(2530, HEIGHT - block_size - 64, 16, 32)
    fire5 = Fire(2625, HEIGHT - block_size - 64, 16, 32)
    fire6 = Fire(3295, HEIGHT - block_size - 64, 16, 32)
    fire7 = Fire(3490, HEIGHT - block_size - 256, 16, 32)
    fire.on() # Turn on the fire. Use .off() to turn off the fire.
    fire2.on()
    fire3.on()
    fire4.on()
    fire5.on()
    fire6.on()
    fire7.on()
    floor = [Block(i * block_size, HEIGHT - block_size, block_size)
             for i in range(-WIDTH // block_size, (WIDTH * 6) // block_size)] # Multiply WIDTH with a larger number to increase the length of the terrain.
    objects = [*floor, Block(0, HEIGHT - block_size * 2, block_size), # Starting point
               Block(0, HEIGHT - block_size * 3, block_size), # This line of code adds a block to the map.
               Block(0, HEIGHT - block_size * 4, block_size),
               Block(0, HEIGHT - block_size * 5, block_size),
               Block(0, HEIGHT - block_size * 6, block_size),
               Block(0, HEIGHT - block_size * 7, block_size),
               Block(0, HEIGHT - block_size * 2, block_size),
               Block(block_size * 5, HEIGHT - block_size * 2, block_size), 
               # Change the number in the first argument to change the position of the block on the x-axis.
               # Change the number in the second argument to change the position of the block on the y-axis.
               Block(block_size * 7, HEIGHT - block_size * 4, block_size),
               Block(block_size * 8, HEIGHT - block_size * 4, block_size), fire,
               Block(block_size * 10, HEIGHT - block_size * 4, block_size), fire2,
               Block(block_size * 11, HEIGHT - block_size * 4, block_size), fire3,
               Block(block_size * 15, HEIGHT - block_size * 2, block_size),
               Block(block_size * 16, HEIGHT - block_size * 2, block_size),
               Block(block_size * 18, HEIGHT - block_size * 2, block_size),
               Block(block_size * 19, HEIGHT - block_size * 2, block_size),
               Block(block_size * 21, HEIGHT - block_size * 2, block_size),
               Block(block_size * 22, HEIGHT - block_size * 3, block_size),
               Block(block_size * 23, HEIGHT - block_size * 4, block_size),
               Block(block_size * 24, HEIGHT - block_size * 5, block_size),
               Block(block_size * 25, HEIGHT - block_size * 5, block_size), fire4,
               Block(block_size * 28, HEIGHT - block_size * 5, block_size), fire5,
               Block(block_size * 29, HEIGHT - block_size * 5, block_size),
               Block(block_size * 30, HEIGHT - block_size * 4, block_size),
               Block(block_size * 31, HEIGHT - block_size * 3, block_size),
               Block(block_size * 32, HEIGHT - block_size * 2, block_size),
               Block(block_size * 35, HEIGHT - block_size * 3, block_size), fire6,
               Block(block_size * 36, HEIGHT - block_size * 3, block_size),
               Block(block_size * 37, HEIGHT - block_size * 3, block_size), fire7] 
            
    offset_x = 0
    # What this means is that when I get to 200 pixels on the left
    # or 200 pixels on the right of the screen, I start scrolling.
    scroll_area_width = 200

    run = True
    while run:
        clock.tick(FPS) # What this line does is ensures that our while loop is going to run 60 frames per second.

        # The first event that we're going to check for is if the user quits the game.
        # If they quit by quitting, I mean they hit the red x in the top right hand corner. 
        # Then we need to stop the event loop and exit our program.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            if event.type == pygame.KEYDOWN:
                # When the user presses the space key, the player jumps.
                if event.key == pygame.K_SPACE and player.jump_count < 2: 
                    player.jump()
                elif event.key == pygame.K_UP and player.jump_count < 2: 
                    player.jump()

        player.loop(FPS)
        fire.loop()
        fire2.loop()
        fire3.loop()
        fire4.loop()
        fire5.loop()
        fire6.loop()
        fire7.loop()
        handle_move(player, objects)
        draw(window, background, bg_image, player, objects, offset_x)

        # The function of this if statement is to scroll to the right or left of the screen
        if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
                (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
            offset_x += player.x_vel

    pygame.quit()
    quit()

# The reason I have this line right here is so that we only call the main function
# if we run this file directly. If we don't run this file directly, say we imported something from it, then we won't run the game code.
if __name__ == "__main__":
    main(window)
