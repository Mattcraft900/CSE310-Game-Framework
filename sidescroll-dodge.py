# Basic arcade shooter

# Imports
import arcade
import random

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Arcade Space Shooter"
SCALING = 2.0
PLAYER_SPEED = 5

class FlyingSprite(arcade.Sprite):
    """Base class for enemies and clouds."""

    def update(self, delta_time: float = 1/60):
        """Move the sprite and remove it when it leaves the screen."""
        self.center_x += self.change_x
        self.center_y += self.change_y

        if self.right < 0:
            self.remove_from_sprite_lists()


class SpaceShooter(arcade.Window):
    """
    Space Shooter side scroller game.

    Player starts on the left, enemies appear on the right.
    Player can move anywhere, but not off screen.
    Enemies fly to the left at variable speed.
    Collisions end the game.
    """

    def __init__(self, width: int, height: int, title: str):
        super().__init__(width, height, title)

        # Modern Arcade style
        self.background_color = arcade.color.SKY_BLUE

        # Sprite lists
        self.enemies_list = arcade.SpriteList()
        self.clouds_list = arcade.SpriteList()
        self.all_sprites = arcade.SpriteList()

        # Game state
        self.paused = False

        # Movement state
        self.up_pressed = False
        self.down_pressed = False
        self.left_pressed = False
        self.right_pressed = False

        self.player = None

        self.setup()

    def setup(self):
        """Prepare the game."""

        # Player
        self.player = arcade.Sprite(
            "images/ship.png",
            scale=SCALING,
            angle=90.0,
        )

        self.player.center_y = self.height / 2
        self.player.left = 10

        self.all_sprites.append(self.player)

        # Spawn timers
        arcade.schedule(self.add_enemy, 0.25)
        arcade.schedule(self.add_cloud, 1.0)

    def add_enemy(self, delta_time: float):
        """Create an enemy."""

        enemy = FlyingSprite(
            "images/asteroid_sm_TL_BR.png",
            scale=SCALING,
        )

        enemy.left = random.randint(self.width, self.width + 80)
        enemy.top = random.randint(10, self.height - 10)

        enemy.change_x = random.randint(-10, -2)

        self.enemies_list.append(enemy)
        self.all_sprites.append(enemy)

    def add_cloud(self, delta_time: float):
        """Create a cloud."""

        cloud = FlyingSprite(
            "images/tile012.png",
            scale=SCALING * 4,
            angle=90,
        )

        cloud.left = random.randint(self.width, self.width + 80)
        cloud.top = random.randint(10, self.height - 10)

        cloud.change_x = random.randint(-5, -2)

        self.clouds_list.append(cloud)
        self.all_sprites.append(cloud)

    def on_key_press(self, symbol: int, modifiers: int):
        """Handle key presses."""

        if symbol == arcade.key.Q:
            self.close()

        elif symbol == arcade.key.P:
            self.paused = not self.paused

        elif symbol in (arcade.key.W, arcade.key.UP):
            self.up_pressed = True

        elif symbol in (arcade.key.S, arcade.key.DOWN):
            self.down_pressed = True

        elif symbol in (arcade.key.A, arcade.key.LEFT):
            self.left_pressed = True

        elif symbol in (arcade.key.D, arcade.key.RIGHT):
            self.right_pressed = True

    def on_key_release(self, symbol: int, modifiers: int):
        """Handle key releases."""

        if symbol in (arcade.key.W, arcade.key.UP):
            self.up_pressed = False

        elif symbol in (arcade.key.S, arcade.key.DOWN):
            self.down_pressed = False

        elif symbol in (arcade.key.A, arcade.key.LEFT):
            self.left_pressed = False

        elif symbol in (arcade.key.D, arcade.key.RIGHT):
            self.right_pressed = False

    def on_update(self, delta_time: float):
        """Update game logic."""

        if self.paused:
            return

        # Calculate player movement from key state
        self.player.change_x = 0
        self.player.change_y = 0

        if self.up_pressed:
            self.player.change_y += PLAYER_SPEED

        if self.down_pressed:
            self.player.change_y -= PLAYER_SPEED

        if self.left_pressed:
            self.player.change_x -= PLAYER_SPEED

        if self.right_pressed:
            self.player.change_x += PLAYER_SPEED

        # Collision check
        if self.player.collides_with_list(self.enemies_list):
            print("Game Over!")
            self.close()

        # Update sprites
        self.all_sprites.update()

        # Keep player on screen
        self.player.left = max(0, self.player.left)
        self.player.right = min(self.width, self.player.right)
        self.player.bottom = max(0, self.player.bottom)
        self.player.top = min(self.height, self.player.top)

    def on_draw(self):
        """Render the frame."""

        self.clear()
        self.all_sprites.draw()

    def on_close(self):
        """Clean up scheduled events before closing."""

        arcade.unschedule(self.add_enemy)
        arcade.unschedule(self.add_cloud)

        super().on_close()


if __name__ == "__main__":
    game = SpaceShooter(
        SCREEN_WIDTH,
        SCREEN_HEIGHT,
        SCREEN_TITLE,
    )

    arcade.run()