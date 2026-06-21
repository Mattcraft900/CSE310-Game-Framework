# Asteroids Clone - CSE310

# Imports
import arcade
import random
import math

# ------ Constants ------ #
# Meta
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Asteroids Clone - CSE310"
SCALING = 1.0
# Player movement
PLAYER_ACCEL = 0.5
BOOST_ACCEL = 1.0
MAX_SPEED = 15.0
FRICTION = 0.95
# Asteroid speeds
AST_MAX_SPEED = 5.0
AST_MIN_SPEED = 1.0
BURST_MAX_SPEED = 5.0
BURST_MIN_SPEED = 0.1
BURST_ANGLE_VARIANCE = 30
# Bullets/firing
BULLET_SPEED = 10.0
BULLET_LIFETIME = 2.0
FIRE_COOLDOWN = 0.50
EXPLOSION_LENGTH = 0.1
# Difficulty settings
BASE_DIFFICULTY = 1.0
DIFFICULTY_MOD = 0.05
# Common magic numbers (to reduce calculation load)
SQRT_TWO = math.sqrt(2)


class Asteroid(arcade.Sprite):
    """Base class for asteroid objects"""
    def __init__(self, path_or_texture = None, scale: float = 1, center_x: float = 0, center_y: float = 0, angle: float = 0, 
                 level: str = 'large', quadrant=None, parent_quadrant=None):
        self.level = level
        self.quadrant = quadrant  # This asteroid's own positional quadrant

        if level == 'large':
            image = "images/asteroid_lg.png"
        elif level == 'medium':
            image = f"images/asteroid_md_{quadrant}.png"
        elif level == 'small':
            # e.g. asteroid_sm_TL_BR.png — parent quadrant first, then own
            image = f"images/asteroid_sm_{parent_quadrant}_{quadrant}.png"
        else:
            raise ValueError(f"Unknown asteroid level: '{level}'")

        super().__init__(image, SCALING)

    # Override update() to check for offscreen positions
    def update(self, delta_time: float = 1/60):
        # Call the parent function
        super().update()
        # enable screenwrap for asteroids
        if self.top < 0:
            self.bottom = SCREEN_HEIGHT
        elif self.bottom > SCREEN_HEIGHT:
            self.top = 0
        if self.right < 0:
            self.left = SCREEN_WIDTH
        elif self.left > SCREEN_WIDTH:
            self.right = 0


class Bullet(arcade.Sprite):
    """Base class for asteroid objects"""
    # Constructor override
    def __init__(self, path_or_texture = None, scale: float = 1):
            super().__init__(path_or_texture, scale)
            self.lifetime = BULLET_LIFETIME

    # Override update() to check for offscreen positions
    def update(self, delta_time: float = 1/60):
        # Call the parent function
        super().update()
        # enable screenwrap for bullets
        if self.top < 0:
            self.bottom = SCREEN_HEIGHT
        elif self.bottom > SCREEN_HEIGHT:
            self.top = 0
        if self.right < 0:
            self.left = SCREEN_WIDTH
        elif self.left > SCREEN_WIDTH:
            self.right = 0

        # Remove bullets whoe lifetime is up
        self.lifetime -= delta_time
        if self.lifetime <= 0:
            self.remove_from_sprite_lists()


class Explosion(arcade.Sprite):
    """Class for Explosion objects (appear upon asteroid destruction)"""
    def __init__(self, level, x, y):
        if level == 'large':
            image = "images/explosion_lg.png"
        elif level == 'medium':
            image = "images/explosion_md.png"
        elif level == 'small':
            image = "images/explosion_sm.png"
        else:
            raise ValueError(f"Unknown explosion level: '{level}'")

        super().__init__(image, SCALING)
        self.center_x = x
        self.center_y = y
        self.lifetime = EXPLOSION_LENGTH

    def update(self, delta_time: float = 1/60):
        self.lifetime -= delta_time
        if self.lifetime <= 0:
            self.remove_from_sprite_lists()


class AsteroidsGame(arcade.Window):
    """
    Basic recreation of the arcade game Asteroids.

    Player starts in the center. 
    Asteroids spawn in randomly out of frame in any direction and fly in at variable speed.
    Player can move anywhere, and wraps around the screen at the borders.
    The player can accelerate in the eight compass directions using WASD/arrow keys, up to a max speed cap.
    The player can fire bullets from the front of their ship.
    Asteroids of medium or large level which are hit by bullets split into 2-4 smaller asteroids.
    Each asteroid destroyed grants a set number of points.
    Difficulty increases over time.
    Collisions end the game.
    """

    # init
    def __init__(self, width: int, height: int, title: str):
        # Call parent initializer
        super().__init__(width, height, title)

        # Background color: black (space aesthetic)
        self.background_color = arcade.color.BLACK

        # Initialize sprite lists
        self.all_sprites = arcade.SpriteList()
        self.asteroid_list = arcade.SpriteList()
        self.bullet_list = arcade.SpriteList()

        # Misc initializers for state vairables
        self.paused = False
        self.up_pressed = False
        self.left_pressed = False
        self.down_pressed = False
        self.right_pressed = False
        self.boost_pressed = False
        self.fire_pressed = False
        self.thruster_state = 'coast'
        self.thrust = PLAYER_ACCEL
        self.fire_timer = 0.0
        self.player = None

        self.setup()

    def setup(self):
        """Prepare the game."""

        # Add the player
        self.player = arcade.Sprite("images/ship.png", SCALING)

        self.player.center_y = self.height / 2
        self.player.center_x = self.width / 2

        self.all_sprites.append(self.player)

        # Thruster/booster sprites
        self.thruster = arcade.Sprite("images/thrusters_001.png", SCALING)
        self.thrust_frames = [arcade.load_texture("images/thrusters_001.png"), arcade.load_texture("images/thrusters_002.png")]
        self.boost_frames = [arcade.load_texture("images/boost_001.png"), arcade.load_texture("images/boost_002.png")]
        self.thrust_frame_index = 0
        self.thrust_timer = 0

        self.all_sprites.append(self.thruster)

        # Set the baseline difficulty
        self.difficulty = BASE_DIFFICULTY

        # Schedule regular asteroid spawns
        arcade.schedule(self.create_asteroid, 6.0)


    def create_asteroid(self, delta_time: float):
        """Create an asteroid."""

        # Create the new asteroid
        asteroid = Asteroid("images/asteroid_sm_TL_BR.png", SCALING)
        
        # 25% chance of each side (t,b,l,r)
        # random area within each side
        # random velocity inward, random angle within 45 degrees of perpendicular
        side = random.randint(1, 4)
        speed = random.random() * (AST_MAX_SPEED - AST_MIN_SPEED) + AST_MIN_SPEED
        entry_angle = random.randint(-45, 45)

        if side == 1: # bottom
            asteroid.top = 0
            asteroid.center_x = random.randint(0, self.width)
            asteroid.angle = 0 + entry_angle
        elif side == 2: # left
            asteroid.right = 0
            asteroid.center_y = random.randint(0, self.height)
            asteroid.angle = 90 + entry_angle
        elif side == 3: # top
            asteroid.bottom = self.height
            asteroid.center_x = random.randint(0, self.width)
            asteroid.angle = 180 + entry_angle
        elif side == 4: # right
            asteroid.left = self.width
            asteroid.center_y = random.randint(0, self.height)
            asteroid.angle = 270 + entry_angle
        
        # Calculate x & y dimensions of the entry velocity
        entry_radians = math.radians(asteroid.angle)
        asteroid.change_x = math.sin(entry_radians) * speed
        asteroid.change_y = math.cos(entry_radians) * speed
        
        # Add the asteroid to the relevant sprite lists
        self.asteroid_list.append(asteroid)
        self.all_sprites.append(asteroid)


    def destroy_asteroid(self, asteroid):
        """Handle asteroid behavior upon destruction."""
        # Spawn explosion at the asteroid's location
        explosion = Explosion(asteroid.level, asteroid.center_x, asteroid.center_y)
        self.all_sprites.append(explosion)

        # Spawn children if not small
        if asteroid.level in ('large', 'medium'):
            child_level = 'medium' if asteroid.level == 'large' else 'small'
            num_children = random.randint(2, 4)
            quadrants = random.sample(['TL', 'TR', 'BL', 'BR'], num_children)
            quadrant_angles = { 'TL': 135, 'TR': 45, 'BL': 225, 'BR': 315, }

            for quadrant in quadrants:
                # Offset child spawn position into its quadrant
                offset = asteroid.width / 4
                ox = offset * (1 if 'R' in quadrant else -1)
                oy = offset * (1 if 'T' in quadrant else -1)

                if asteroid.level == 'large':
                    child = Asteroid(level=child_level, quadrant=quadrant)
                else:
                    child = Asteroid(level=child_level, quadrant=quadrant, parent_quadrant=asteroid.quadrant)

                child.center_x = asteroid.center_x + ox
                child.center_y = asteroid.center_y + oy
                child.angle = random.randint(0, 359)

                # Random outward velocity
                speed = random.uniform(BURST_MIN_SPEED, BURST_MAX_SPEED)
                center_angle = quadrant_angles[quadrant]
                angle_rad = math.radians(random.uniform(center_angle - BURST_ANGLE_VARIANCE, center_angle + BURST_ANGLE_VARIANCE))
                child.change_x = math.cos(angle_rad) * speed
                child.change_y = math.sin(angle_rad) * speed

                self.asteroid_list.append(child)
                self.all_sprites.append(child)

        asteroid.remove_from_sprite_lists()


    def fire_bullet(self, delta_time: float = 1/60):
        """Fire a bullet from the front of the ship."""

        # If less than a second has passed since the last bullet was fired, don't fire.
        # if delta_time < 1.0:
        #     return

        # Create the new bullet object
        bullet = Bullet('images/bullet.png', SCALING)

        # Calculate bullet's position
        offset = self.player.height / 2 * SCALING
        angle_rad = math.radians(self.player.angle)
        offset_x = math.sin(angle_rad) * offset
        offset_y = math.cos(angle_rad) * offset
        bullet.center_x = self.player.center_x + offset_x
        bullet.center_y = self.player.center_y + offset_y
        # Set the bullet's angle to be the same as the ship's
        bullet.angle = self.player.angle

        # Calculate the bullet's speed
        speed = BULLET_SPEED + math.hypot(self.player.change_x, self.player.change_y)
        bullet.change_x = math.sin(angle_rad) * speed
        bullet.change_y = math.cos(angle_rad) * speed

        self.bullet_list.append(bullet)
        self.all_sprites.append(bullet)



    def on_key_press(self, symbol: int, modifiers: int):
        """Handle key presses."""

        # Quit button
        if symbol in (arcade.key.Q, arcade.key.ESCAPE):
            self.close()

        # Pause buttons
        elif symbol in (arcade.key.P, arcade.key.E):
            self.paused = not self.paused

        # Directional keys
        elif symbol in (arcade.key.W, arcade.key.UP):
            self.up_pressed = True
        elif symbol in (arcade.key.S, arcade.key.DOWN):
            self.down_pressed = True
        elif symbol in (arcade.key.A, arcade.key.LEFT):
            self.left_pressed = True
        elif symbol in (arcade.key.D, arcade.key.RIGHT):
            self.right_pressed = True
        
        # Boost key
        elif symbol in (arcade.key.LSHIFT, arcade.key.RSHIFT):
            self.boost_pressed = True

        # Fire key
        elif symbol == arcade.key.SPACE:
            self.fire_pressed = True


    def on_key_release(self, symbol: int, modifiers: int):
        """Handle key releases."""

        # Directional keys
        if symbol in (arcade.key.W, arcade.key.UP):
            self.up_pressed = False
        elif symbol in (arcade.key.S, arcade.key.DOWN):
            self.down_pressed = False
        elif symbol in (arcade.key.A, arcade.key.LEFT):
            self.left_pressed = False
        elif symbol in (arcade.key.D, arcade.key.RIGHT):
            self.right_pressed = False
        
        # Boost key
        elif symbol in (arcade.key.LSHIFT, arcade.key.RSHIFT):
            self.boost_pressed = False

        # Fire key
        elif symbol == arcade.key.SPACE:
            self.fire_pressed = False
    

    def on_update(self, delta_time: float):
        """Update game logic."""

        # Being paused causes the game to freeze until unpaused
        if self.paused:
            return

        # ----- Calculate player movement ----- #
        # Acceleration based on key states
        # (Moving diagonally happens at the same rate as orthogonally)
        dx, dy = 0, 0
        # Using add/subtract instead of assignment to handle when opposite directions are both pressed
        if self.up_pressed: dy += 1
        if self.down_pressed: dy -= 1
        if self.right_pressed: dx += 1
        if self.left_pressed: dx -= 1
        # Normalize diagonal movement speed
        length = math.hypot(dx, dy)
        if length > 0:
            dx /= length
            dy /= length
        # Apply boost acceleration if space bar is held
        if self.boost_pressed:
            dx *= BOOST_ACCEL
            dy *= BOOST_ACCEL
        else:
            dx *= PLAYER_ACCEL
            dy *= PLAYER_ACCEL

        # Apply the calculated speeds
        self.player.change_x += dx
        self.player.change_y += dy
        # Apply friction
        self.player.change_x *= FRICTION
        self.player.change_y *= FRICTION

        # Enable screen wrap
        if self.player.top < 0:
            self.player.bottom = self.height
        elif self.player.bottom > self.height:
            self.player.top = 0
        if self.player.right < 0:
            self.player.left = self.width
        elif self.player.left > self.width:
            self.player.right = 0

        # Update ship sprite rotation
        if dx != 0 or dy != 0:
            angle_rad = math.atan2(dx, dy)
            self.player.angle = math.degrees(angle_rad)
            if self.boost_pressed:
                self.thruster_state = 'boost'
            else:
                self.thruster_state = 'thrust'
        else:
            self.thruster_state = 'coast'

        # ------ Thruster/booster sprites ------ #
        ANIM_SPEED = 6
        self.thruster.visible = True
        if self.thruster_state in ('thrust', 'boost'):
            self.thrust_timer += 1
            if self.thrust_timer >= ANIM_SPEED:
                self.thrust_timer = 0
                self.thrust_frame_index = (
                    self.thrust_frame_index + 1
                ) % len(self.thrust_frames)

        offset_distance = self.player.height * SCALING / 2.0
        rad = math.radians(self.player.angle)

        math_angle = math.atan2(dy, dx)
        rad = math_angle  # keep math angle for vectors

        offset_x = -math.cos(rad) * offset_distance
        offset_y = -math.sin(rad) * offset_distance

        self.thruster.center_x = self.player.center_x + offset_x
        self.thruster.center_y = self.player.center_y + offset_y
        self.thruster.angle = self.player.angle

        if self.thruster_state == 'thrust':
            self.thruster.texture = self.thrust_frames[self.thrust_frame_index]
        elif self.thruster_state == 'boost':
            self.thruster.texture = self.boost_frames[self.thrust_frame_index]
        else:
            self.thruster.visible = False

        # Collision check
        if self.player.collides_with_list(self.asteroid_list):
            print("Game Over!")
            self.close()

        # Handle bullet-firing, including cooldown
        self.fire_timer -= delta_time
        if self.fire_pressed and self.fire_timer <= 0:
            self.fire_bullet()
            self.fire_timer = FIRE_COOLDOWN

        for bullet in self.bullet_list:
            hit_list = bullet.collides_with_list(self.asteroid_list)
            if hit_list:
                bullet.remove_from_sprite_lists()
                for asteroid in hit_list:
                    self.destroy_asteroid(asteroid)
        
        # Update all sprites
        self.all_sprites.update(delta_time)
    

    def on_draw(self):
        """Render the frame."""

        self.clear()
        self.all_sprites.draw()


    def on_close(self):
        """Clean up scheduled events before closing."""

        arcade.unschedule(self.create_asteroid)

        super().on_close()


if __name__ == "__main__":
    game = AsteroidsGame(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

    arcade.run()
