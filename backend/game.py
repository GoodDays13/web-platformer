import asyncio
from dataclasses import dataclass

from constants import CANVAS_W, GRAVITY, PLAYER_SPEED, PLAYER_ACCELERATION, JUMP_VELOCITY, JUMP_DURATION, COYOTE_TIME, PLAYER_SIZE

class Game:
    player: GameObject
    platforms: list[GameObject]
    held_keys: set[str]

    grounded: bool
    coyote: float
    jumping: bool

    def __init__(self) -> None:
        self.player = GameObject(0, 0, 0, 0, PLAYER_SIZE, PLAYER_SIZE)
        self.platforms = [
            GameObject(0, 64, 0, 0, 32, 32),
            GameObject(256, 128, 0, 0, 64, 32)
        ]
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
                asyncio.get_event_loop().call_later(JUMP_DURATION, self.stop_jump)
            else:
                self.jumping = False

    def update(self, delta_time):
        self.coyote = max(0, self.coyote - delta_time)

        velocity_target_x = 0
        if 'KeyA' in self.held_keys:
            velocity_target_x -= PLAYER_SPEED
        if 'KeyD' in self.held_keys:
            velocity_target_x += PLAYER_SPEED

        velocity_diff = velocity_target_x - self.player.velocity_x
        if velocity_diff != 0:
            sign = abs(velocity_diff) / velocity_diff
            velocity_diff = abs(velocity_diff)
            self.player.velocity_x += sign * min(velocity_diff, PLAYER_ACCELERATION * delta_time)

        if self.jumping:
            self.player.velocity_y = JUMP_VELOCITY
        else:
            self.player.velocity_y -= GRAVITY * delta_time

        prev_x = self.player.x
        prev_y = self.player.y

        self.player.x += self.player.velocity_x * delta_time
        self.player.y += self.player.velocity_y * delta_time

        self.grounded = False

        if self.player.y < 0:
            self.player.y = 0
            self.grounded = True
            self.player.velocity_y = 0

        for platform in self.platforms:
            if overlaps(self.player, platform):
                if prev_y >= platform.y + platform.height:
                    self.player.y = platform.y + platform.height
                    self.player.velocity_y = 0
                    self.grounded = True
                    self.coyote = COYOTE_TIME
                elif prev_y + self.player.height <= platform.y:
                    self.player.y = platform.y - self.player.height
                    self.player.velocity_y = 0
                    self.jumping = False
                elif prev_x + self.player.width <= platform.x:
                    self.player.x = platform.x - self.player.width
                elif prev_x >= platform.x + platform.width:
                    self.player.x = platform.x + platform.width

        if self.player.x < 0:
            self.player.x = 0
            self.player.velocity_x = 0
        elif self.player.x + self.player.width > CANVAS_W:
            self.player.x = CANVAS_W - self.player.width
            self.player.velocity_x = 0


# y is up, (x, y) is bottom-left
@dataclass
class GameObject:
    x: float
    y: float
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
