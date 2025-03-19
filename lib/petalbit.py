"""Drifting petals in the wind."""

import random
from time import sleep

from adafruit_clue import clue
from adafruit_is31fl3731.scroll_phat_hd import ScrollPhatHD as Display


class Petal:
    def __init__(
        self, x: int = 0, y: int = 0, brightness: int = 255, decay_rate: int = 1
    ):
        self.x: int = x
        self.y: int = y
        self.brightness: int = brightness
        self.decay_rate: int = decay_rate

        self.dead: bool = False

    def decay(self):
        self.brightness = max(0, self.brightness - self.decay_rate)
        self.dead = not bool(self.brightness)
        return self.brightness

    def draw(self, display: Display):
        if (self.x > display.width) or (self.y > display.height):
            self.dead = True
            return
        display.pixel(self.x, self.y, self.brightness)


class Edge:
    top: int = 0
    bottom: int = 1
    left: int = 2
    right: int = 3

    def __init__(self, width: int, height: int, side: int = top):
        self.side: int = side
        self.height: int = height
        self.width: int = width

    def pixel_pen(self):
        """Return pixel boundaries for selected edge.

        Resulting tuple will be set notation of integers, inclusive.

        - top: x = [0, width], y = [0, 0]
        - bottom: x = [0, width], y = [height, height]
        - left: x = [0, 0], y = [0, height]
        - right: x = [width, width], y = [0, height]

        """
        if self.side == self.top:
            return ((0, self.width), (0, 0))
        elif self.side == self.bottom:
            return ((0, self.width), (self.height, self.height))
        elif self.side == self.left:
            return ((0, 0), (0, self.height))
        else:  # right
            return ((self.width, self.width), (0, self.height))

    def apply_gravity(self, x: int, y: int):
        """Move pixel according to gravity."""
        if self.side == self.top:
            return x, y + 1
        elif self.side == self.bottom:
            return x, y - 1
        elif self.side == self.left:
            return x + 1, y
        else:  # right
            return x - 1, y


class Wind:
    """Control the wind behaviour.

    Args:
        edge: Display edge controller.
        gust_chance: Higher number creates more gusts.
        gust_duration_max: Higher number allow potentially longer gusts.
        gust_miss_chance: Higher number blows less petals.
        gust_strength_max: Higher number allows potentially stronger gusts.

    """

    def __init__(
        self,
        edge: Edge,
        gust_chance: float = 0.5,
        gust_duration_max: int = 4,
        gust_miss_chance: float = 0.5,
        gust_strength_max: int = 1,
    ):
        self.edge: Edge = edge

        self.gust_chance: float = gust_chance
        self.gust_duration_max: int = gust_duration_max
        self.gust_miss_chance: float = gust_miss_chance
        self.gust_strength_max: int = gust_strength_max

        self.gust_blowing: int = 0
        self.gust_strength: int = 0

    def blow(self, petals: list[Petal]):
        """Blow petals to a side."""
        if random.random() > self.gust_chance:
            return

        if self.gust_blowing < 1:
            # Create a gust of wind.
            self.gust_blowing = random.randint(0, self.gust_duration_max)
            gust_strengths = list(
                range(-self.gust_strength_max, self.gust_strength_max + 1)
            )
            self.gust_strength = random.choice(gust_strengths)

        for petal in petals:
            if random.random() < self.gust_miss_chance:
                continue

            if self.edge.side in (self.edge.top, self.edge.bottom):
                petal.x += self.gust_strength
            else:  # left or right
                petal.y += self.gust_strength

        # Gust of wind slowly dies down.
        self.gust_blowing -= 1


class PetalDisplay:
    def __init__(
        self,
        edge: Edge,
        wind: Wind,
        petal_brightness_max: int = 255,
        petal_brightness_min: int = 100,
        petal_decay_rate_max: int = 30,
        petal_drift_chance: float = 0.5,
    ):
        self.edge: Edge = edge
        self.wind: Wind = wind

        self.petal_brightness_max: int = petal_brightness_max
        self.petal_brightness_min: int = petal_brightness_min
        self.petal_decay_rate_max: int = petal_decay_rate_max
        self.petal_drift_chance: float = petal_drift_chance

    def bloom(self):
        x_pen, y_pen = self.edge.pixel_pen()
        x = random.randint(*x_pen)
        y = random.randint(*y_pen)

        return Petal(
            x=x,
            y=y,
            brightness=random.randint(
                self.petal_brightness_min, self.petal_brightness_max
            ),
            decay_rate=random.randint(0, self.petal_decay_rate_max),
        )

    def drop(self, petal: Petal):
        """Apply gravity to petal."""
        if random.random() < self.petal_drift_chance:
            return

        petal.x, petal.y = self.edge.apply_gravity(petal.x, petal.y)

    def gust(self, petals: list[Petal]):
        """Blow petals to a side."""
        self.wind.blow(petals)


def more_blooms(chance: float = 0.0):
    """Add more petals when :obj:`True`."""
    return random.random() > chance


def main(
    frames_per_second: int = 10,
    bloom_chance: float = 0.3,
    petals_per_bloom_max: int = 3,
):
    display = Display(clue._i2c)

    speed = 1 / max(frames_per_second, 1)  # Prevent division by zero / negative

    edge = Edge(width=display.width, height=display.height, side=Edge.top)

    wind = Wind(
        edge=edge,
        gust_chance=0.2,
        gust_duration_max=5,
        gust_miss_chance=0.4,
        gust_strength_max=2,
    )

    petal_display = PetalDisplay(
        edge=edge,
        petal_brightness_max=200,
        petal_brightness_min=50,
        petal_decay_rate_max=20,
        petal_drift_chance=0.8,
        wind=wind,
    )

    petals = [petal_display.bloom()]

    frame = False

    while True:
        display.frame(frame, show=False)
        display.fill(0)

        for petal in petals:
            petal.draw(display)
            petal.decay()
            petal_display.drop(petal)

        display.frame(frame, show=True)
        sleep(speed)

        petals = [petal for petal in petals if not petal.dead]

        if more_blooms(chance=bloom_chance):
            new_petals = [
                petal_display.bloom()
                for _ in range(random.randint(0, petals_per_bloom_max))
            ]
            petals.extend(new_petals)

        petal_display.gust(petals)

        # if random.random() > 0.9:
        #     edge.side = random.choice([edge.top, edge.bottom, edge.left, edge.right])

        frame = not frame
