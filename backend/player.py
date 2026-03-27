class Player:
    # left
    x: float
    # bottom
    y: float
    # velocity
    velocity_x: float
    velocity_y: float
    velocity_target_x: float
    size_x: float
    size_y: float

    grounded: bool
    jumping: bool

    def __init__(self) -> None:
        self.x = 0
        self.y = 0
        self.velocity_x = 0
        self.velocity_y = 0
        self.velocity_target_x = 0
        self.size_x = 32
        self.size_y = 32
        self.grounded = False
        self.jumping = False
