import asyncio
from dataclasses import dataclass

from constants import CANVAS_W

GRAVITY = 4096

class Game:
    player: GameObject
    platforms: list[GameObject]
    held_keys: set[str]

    grounded: bool
    coyote: float
    jumping: bool

    def __init__(self) -> None:
        self.player = GameObject(0, 0, 0, 0, 32, 32)
        self.platforms = [ GameObject(0, 64, 0, 0, 32, 32) ]
        self.held_keys = set()
        self.grounded = False
        self.coyote = 0
        self.jumping = False

    def stop_jump(self):
        self.jumping = False

    def handle_input(self, key, down):
        if key == 'Space':
            if down and (self.grounded or self.coyote):
                self.jumping = True
                self.grounded = False
                asyncio.get_event_loop().call_later(.15, self.stop_jump)
            else:
                self.jumping = False

    def update(self, delta_time):
        self.coyote = max(0, self.coyote - delta_time)

        velocity_target_x = 0
        if 'KeyA' in self.held_keys:
            velocity_target_x -= 512
        if 'KeyD' in self.held_keys:
            velocity_target_x += 512

        velocity_diff = velocity_target_x - self.player.velocity_x
        if velocity_diff != 0:
            sign = abs(velocity_diff) / velocity_diff
            velocity_diff = abs(velocity_diff)
            self.player.velocity_x += sign * min(velocity_diff, 3072 * delta_time)

        # Set velocity based on either jumping or gravity
        if self.jumping:
            self.player.velocity_y = 512
        else:
            self.player.velocity_y -= GRAVITY * delta_time # gravity

        prev_x = self.player.x
        prev_y = self.player.y

        # Move based on velocity
        self.player.x += self.player.velocity_x * delta_time
        self.player.y += self.player.velocity_y * delta_time

        self.grounded = False

        # Absolute floor collision
        if self.player.y < 0:
            self.player.y = 0
            self.grounded = True
            self.player.velocity_y = 0

        # Platform collisions
        for platform in self.platforms:
            if overlaps(self.player, platform):
                # Which side did we enter from?
                # Check where the self.player was BEFORE this tick
                if prev_y >= platform.y + platform.height:  # was above, entered from top
                    self.player.y = platform.y + platform.height  # push back up
                    self.player.velocity_y = 0
                    self.grounded = True
                    self.coyote = .05
                elif prev_y + self.player.height <= platform.y:  # was below, entered from bottom
                    self.player.y = platform.y - self.player.height
                    self.player.velocity_y = 0
                    self.jumping = False
                elif prev_x + self.player.width <= platform.x:  # left side
                    self.player.x = platform.x - self.player.width
                elif prev_x >= platform.x + platform.width:  # right side
                    self.player.x = platform.x + platform.width

        # Absolute walls collision
        if self.player.x < 0:
            self.player.x = 0
            self.player.velocity_x = 0
        elif self.player.x + self.player.width > CANVAS_W:
            self.player.x = CANVAS_W - self.player.width
            self.player.velocity_x = 0


@dataclass
class GameObject:
    # left
    x: float
    # bottom
    y: float
    # velocity
    velocity_x: float
    velocity_y: float
    width: float
    height: float

def overlaps(first: GameObject, second: GameObject) -> bool:
    return (
        first.x < second.x + second.width and
        first.x + first.width > second.x and
        first.y < second.y + second.height and
        first.y + first.height > second.y
    )
