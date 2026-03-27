import asyncio
from player import Player

GRAVITY = 64

class Game:
    player: Player
    held_keys: set

    def __init__(self) -> None:
        self.player = Player()
        self.held_keys = set()

    def stop_jump(self):
        self.player.jumping = False

    def handle_input(self, key, down):
        if key == 'Space':
            if down and self.player.grounded:
                self.player.jumping = True
                self.player.grounded = False
                asyncio.get_event_loop().call_later(.15, self.stop_jump)
            else:
                self.player.jumping = False

    def update(self, delta_time):
        self.player.velocity_target_x = 0
        if 'KeyA' in self.held_keys:
            self.player.velocity_target_x -= 512
        if 'KeyD' in self.held_keys:
            self.player.velocity_target_x += 512

        velocity_diff = self.player.velocity_target_x - self.player.velocity_x
        if velocity_diff != 0:
            sign = abs(velocity_diff) / velocity_diff
            velocity_diff = abs(velocity_diff)
            self.player.velocity_x += sign * min(velocity_diff, 32)

        if self.player.jumping:
            self.player.velocity_y = 512
        elif not self.player.grounded:
            self.player.velocity_y -= GRAVITY # gravity

        self.player.x += self.player.velocity_x * delta_time
        self.player.y += self.player.velocity_y * delta_time

        if self.player.y < 0:
            self.player.y = 0
            self.player.grounded = True
            self.player.velocity_y = 0

        if not self.player.grounded:
            self.player.velocity_y -= 1 * delta_time
