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

    def draw(self, display: Display, frame: int = 0):
        if (self.x > display.width) or (self.y > display.height):
            self.dead = True
            return
        display.pixel(self.x, self.y, self.brightness, frame=frame)


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


class Layer:
    def __init__(
        self,
        edge: Edge,
        wind: Wind,
        bloom_chance: float = 0.5,
        petal_brightness_max: int = 255,
        petal_brightness_min: int = 10,
        petal_decay_rate_max: int = 10,
        petal_drift_chance: float = 0.5,
        petals_per_bloom_max: int = 1,
        petals: list[Petal] = None,
    ):
        self.edge: Edge = edge
        self.wind: Wind = wind

        self.bloom_chance: float = bloom_chance

        assert 0 <= petal_brightness_min <= petal_brightness_max <= 255, (
            f"Petal brightness must be 0 <= {petal_brightness_min=} <= {petal_brightness_max=} <= 255"
        )
        self.petal_brightness_min: int
        self.petal_brightness_max: int
        self.petal_brightness_min, self.petal_brightness_max = sorted(
            [petal_brightness_min, petal_brightness_max]
        )

        self.petal_decay_rate_max: int = petal_decay_rate_max
        self.petal_drift_chance: float = petal_drift_chance
        self.petals_per_bloom_max: int = petals_per_bloom_max
        self.petals: list[Petal] = petals or []

    def bloom(self):
        """Create a petal."""
        x_pen, y_pen = self.edge.pixel_pen()
        x = random.randint(*x_pen)
        y = random.randint(*y_pen)

        brightness = random.randint(
            self.petal_brightness_min, self.petal_brightness_max
        )
        decay_rate = random.randint(0, self.petal_decay_rate_max)
        return Petal(x=x, y=y, brightness=brightness, decay_rate=decay_rate)

    def clean_petals(self):
        """Remove dead petals."""
        self.petals = [petal for petal in self.petals if not petal.dead]

    def draw(self, display: Display, frame: int = 0):
        """Draw petals on dispaly."""
        for petal in self.petals:
            petal.draw(display, frame=frame)

    def decay(self):
        """Fading petals."""
        for petal in self.petals:
            if random.random() > 0.9:
                continue

            petal.decay()

    def drop(self):
        """Apply gravity to petals."""
        for petal in self.petals:
            if random.random() < self.petal_drift_chance:
                continue

            petal.x, petal.y = self.edge.apply_gravity(petal.x, petal.y)

    def generate_blooms(self):
        """Create more petals."""
        if not more_blooms(chance=self.bloom_chance):
            return

        number_of_petals = random.randint(0, self.petals_per_bloom_max)
        new_petals = [self.bloom() for _ in range(number_of_petals)]
        self.petals.extend(new_petals)

    def gust(self):
        """Blow petals."""
        self.wind.blow(self.petals)


class LayeredPetalDisplay:
    def __init__(
        self,
        edge: Edge,
        wind: Wind,
        bloom_chance: float = 0.5,
        brightness_max: int = 255,
        brightness_min: int = 0,
        num_of_layers: int = 1,
        petals_per_bloom_max: int = 2,
    ):
        self.edge: Edge = edge
        self.wind: Wind = wind

        self.bloom_chance: float = bloom_chance
        self.brightness_max: int = brightness_max
        self.brightness_min: int = brightness_min
        self.num_of_layers: int = num_of_layers
        self.petals_per_bloom_max: int = petals_per_bloom_max

        self.brightness_brackets = tuple(
            range(
                self.brightness_min,
                self.brightness_max + 1,  # +1 to make range inclusive
                (self.brightness_max - self.brightness_min) // self.num_of_layers,
            )
        )

        self.layers: list[Layer] = []

    def apply_effect(self, func):
        """Run function on layers."""
        for layer in self.layers:
            for petal in layer.petals:
                func(petal)

    def create_layers(self):
        """Set up number of layers with petals."""
        for num in range(self.num_of_layers):
            petal_brightness_min = self.brightness_brackets[num]
            petal_brightness_max = self.brightness_brackets[num + 1]

            layer = Layer(
                self.edge,
                self.wind,
                bloom_chance=self.bloom_chance,
                petal_brightness_max=petal_brightness_max,
                petal_brightness_min=petal_brightness_min,
                petal_decay_rate_max=10,
                petal_drift_chance=0.5,
                petals_per_bloom_max=self.petals_per_bloom_max,
                petals=[],
            )
            layer.generate_blooms()

            self.layers.append(layer)

        return self.layers

    def draw(self, display: Display, frame: int = 0):
        """Draw layers on display."""
        first_layer, *_ = self.layers

        for layer in self.layers:
            layer.draw(display, frame=frame)
            layer.decay()
            layer.drop()
            layer.clean_petals()
            layer.generate_blooms()

            if layer == first_layer:
                layer.gust()


def more_blooms(chance: float = 0.0):
    """Add more petals when :obj:`True`."""
    return random.random() > chance


def main(
    bloom_chance: float = 0.3,
    frames_per_second: int = 10,
    gust_chance: float = 0.7,
    gust_duration_max: int = 10,
    gust_miss_chance: float = 0.3,
    gust_strength_max: int = 3,
    num_of_layers: int = 3,
    petals_per_bloom_max: int = 2,
):
    speed = 1 / max(frames_per_second, 1)  # Prevent division by zero / negative

    display = Display(clue._i2c)

    edge = Edge(width=display.width, height=display.height, side=Edge.top)

    wind = Wind(
        edge=edge,
        gust_chance=gust_chance,
        gust_duration_max=gust_duration_max,
        gust_miss_chance=gust_miss_chance,
        gust_strength_max=gust_strength_max,
    )

    layered_petal_display = LayeredPetalDisplay(
        edge,
        wind,
        bloom_chance=bloom_chance,
        brightness_min=10,
        brightness_max=200,
        num_of_layers=num_of_layers,
        petals_per_bloom_max=petals_per_bloom_max,
    )
    layered_petal_display.create_layers()

    frame = False

    while True:
        display.frame(frame, show=False)
        display.fill(0)

        layered_petal_display.draw(display, frame=frame)

        display.frame(frame, show=True)
        sleep(speed)

        frame = not frame
