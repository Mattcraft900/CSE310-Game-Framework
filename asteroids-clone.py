# Asteroids Clone - CSE310

# Imports
import arcade
import random
import math

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Asteroids Clone - CSE310"
SCALING = 1.0

# Arbitrary constants, these probably need tweaking later
PLAYER_ACCEL = 0.5
BOOST_ACCEL = 1.0
MAX_SPEED = 15.0
AST_SPEED = 5.0
AST_BURST_SPEED = 5.0
FRICTION = 0.99

BASE_DIFFICULTY = 1.0

# Magic numbers
SQRT_TWO = math.sqrt(2)


class AsteroidsGame(arcade.Window):
    """
    Basic recreation of the arcade game Asteroids.

    Player starts in the center. 
    Asteroids spawn in randomly out of frame in any direction and fly in at variable speed.
    Player can move anywhere, and wraps around the screen at the borders.
    The player can accelerate in the eight compass directions using WASD/arrow keys, up to a max speed cap.
    The player can fire bullets from the front of their ship.
    Asteroids of medium or large size which are hit by bullets split into 2-4 smaller asteroids.
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
        self.space_pressed = False
        self.thruster_state = 'coast'
        self.thrust = PLAYER_ACCEL
        self.player = None

        self.setup()

    def setup(self):
        """Prepare the game."""

        # Add the player
        self.player = arcade.Sprite("images/ship.png", SCALING)

        print(self.player.height)
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


    def on_key_press(self, symbol: int, modifiers: int):
        """Handle key presses."""

        # Quit button
        if symbol == arcade.key.Q:
            self.close()

        # Pause buttons
        elif symbol in (arcade.key.P, arcade.key.ESCAPE):
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
        elif symbol == arcade.key.SPACE:
            self.space_pressed = True

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
        elif symbol == arcade.key.SPACE:
            self.space_pressed = False
    

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
        if self.space_pressed:
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
            if self.space_pressed:
                self.thruster_state = 'boost'
            else:
                self.thruster_state = 'thrust'
        else:
            self.thruster_state = 'coast'

        # Thruster/booster sprites
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
        
        # Update sprites
        self.all_sprites.update()
    

    def on_draw(self):
        """Render the frame."""

        self.clear()
        self.all_sprites.draw()


    def on_close(self):
        """Clean up scheduled events before closing."""

        # arcade.unschedule(self.add_enemy)

        super().on_close()


if __name__ == "__main__":
    game = AsteroidsGame(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

    arcade.run()
