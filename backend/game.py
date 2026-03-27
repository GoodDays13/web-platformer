import asyncio
from dataclasses import dataclass

from constants import CANVAS_W

GRAVITY = 4096

class Game:
    player: GameObject
    held_keys: set

    grounded: bool
    jumping: bool

    def __init__(self) -> None:
        self.player = GameObject(0, 0, 0, 0, 32, 32)
        self.held_keys = set()
        self.grounded = False
        self.jumping = False

    def stop_jump(self):
        self.jumping = False

    def handle_input(self, key, down):
        if key == 'Space':
            if down and self.grounded:
                self.jumping = True
                self.grounded = False
                asyncio.get_event_loop().call_later(.15, self.stop_jump)
            else:
                self.jumping = False

    def update(self, delta_time):
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

        if self.jumping:
            self.player.velocity_y = 512
        elif not self.grounded:
            self.player.velocity_y -= GRAVITY * delta_time # gravity

        self.player.x += self.player.velocity_x * delta_time
        self.player.y += self.player.velocity_y * delta_time

        if self.player.y < 0:
            self.player.y = 0
            self.grounded = True
            self.player.velocity_y = 0

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

