import asyncio
from dataclasses import dataclass

from constants import CANVAS_W, CANVAS_H, GRAVITY, PLAYER_SPEED, PLAYER_ACCELERATION, JUMP_VELOCITY, JUMP_DURATION, COYOTE_TIME, PLAYER_SIZE

class Game:
    timeout: asyncio.Task
    player: GameObject
    platforms: list[GameObject]
    camera_y: float
    held_keys: set[str]

    grounded: bool
    coyote: float
    jumping: bool

    def __init__(self, timeout: asyncio.Task) -> None:
        self.timeout = timeout
        self.player = GameObject(0, 0, 0, 0, PLAYER_SIZE, PLAYER_SIZE)
        self.platforms = [
            GameObject(0, 64, 0, 0, 32, 32),
            GameObject(256, 64 * 2, 0, 0, 64, 32),
            GameObject(544, 64 * 3, 0, 0, 32, 32),
            GameObject(544 + 64, 64 * 4.5, 0, 0, 32, 32),
            GameObject(544 + 64 * 2, 64 * 6, 0, 0, 32, 32),
            GameObject(CANVAS_W - 16, 64 * 7.5, 0, 0, 32, 32),
            GameObject(576, 64 * 9, 0, 0, 32, 32),
            GameObject(576 - 32 * 3, 64 * 10.5, 0, 0, 32 * 4, 32),
            GameObject(256, 64 * 5, 0, 0, 64, 32),
            GameObject(256 + 32, 64 * 6, 0, 0, 32, 32),
            GameObject(256, 64 * 7, 0, 0, 32, 32),
            GameObject(256 + 32, 64 * 8, 0, 0, 32, 32),
            GameObject(256, 64 * 9, 0, 0, 32, 32),
            GameObject(256 - 128, 64 * 9, 0, 0, 32, 32),
        ]
        self.camera_y = 0
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
            self.player.velocity_x += sign * min(velocity_diff, (PLAYER_ACCELERATION if self.grounded else PLAYER_ACCELERATION * .3) * delta_time)

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
                    self.player.velocity_x = 0
                elif prev_x >= platform.x + platform.width:
                    self.player.x = platform.x + platform.width
                    self.player.velocity_x = 0

        if self.player.x < 0:
            self.player.x = 0
            self.player.velocity_x = 0
        elif self.player.x + self.player.width > CANVAS_W:
            self.player.x = CANVAS_W - self.player.width
            self.player.velocity_x = 0

        target_camera_y = self.player.y - (CANVAS_H / 2 - self.player.width)
        camera_delta_y = target_camera_y - self.camera_y
        self.camera_y += camera_delta_y * 10 * delta_time
        self.camera_y = max(0, self.camera_y)


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
