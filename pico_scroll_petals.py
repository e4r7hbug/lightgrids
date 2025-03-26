"""For Pimorono Pico Scroll Pack with RP2040 running MicroPython.

- https://shop.pimoroni.com/products/pico-scroll-pack
- https://github.com/pimoroni/pimoroni-pico/releases

"""

import math
import random
import time

from picoscroll import HEIGHT, WIDTH, PicoScroll

scroll = PicoScroll()


class Petal:
    def __init__(
        self,
        x: float,
        y: float,
        max_width: int,
        max_height: int,
        steps_per_interval: int,
        drop_direction_x: int = 0,
        drop_direction_y: int = 1,
    ):
        self.x: float = x
        self.y: float = y
        self.max_width: int = max_width
        self.max_height: int = max_height
        self.steps_per_interval: int = steps_per_interval

        self.drop_direction_x: int = drop_direction_x
        self.drop_direction_y: int = drop_direction_y
        self.drop_increment: float = random.random() / self.steps_per_interval

        self.x_drops: list[float] = []
        self.y_drops: list[float] = []

        self.x_steps: list[float] = []
        self.y_steps: list[float] = []

    def grid(self):
        """Return grid of points to draw.

        1 0
        0 0

        """
        x_dec, x = math.modf(self.x)
        y_dec, y = math.modf(self.y)
        x, y = int(x), int(y)

        top_left = (
            x % self.max_width,
            y % self.max_height,
            ((1 - x_dec) * (1 - y_dec)),
        )
        top_right = (
            (x + 1) % self.max_width,
            y % self.max_height,
            (x_dec * (1 - y_dec)),
        )

        bottom_left = (
            x % self.max_width,
            (y + 1) % self.max_height,
            ((1 - x_dec) * y_dec),
        )
        bottom_right = (
            (x + 1) % self.max_width,
            (y + 1) % self.max_height,
            (x_dec * y_dec),
        )

        return (top_left, top_right, bottom_left, bottom_right)

    def step_size(self):
        step = random.randrange(-10, 10) / 10
        return step / self.steps_per_interval

    def walk(self):
        if not self.x_steps:
            self.x_steps = [self.step_size()] * self.steps_per_interval
        if not self.y_steps:
            self.y_steps = [self.step_size()] * self.steps_per_interval

        self.x = (self.x + self.x_steps.pop()) % self.max_width
        self.y = (self.y + self.y_steps.pop()) % self.max_height
        return self.x, self.y

    def drop(self):
        if not self.x_drops:
            self.x_drops = [
                self.drop_direction_x * self.drop_increment
            ] * self.steps_per_interval
        if not self.y_drops:
            self.y_drops = [
                self.drop_direction_y * self.drop_increment
            ] * self.steps_per_interval

        # drift
        if random.random() < 0.1:
            # self.x_drops.pop()
            drift_frames = random.randrange(5)
            self.x_drops = [self.step_size()] * drift_frames + self.x_drops
            self.y_drops = [0] * drift_frames + self.y_drops
            # return

        self.x = (self.x + self.x_drops.pop()) % self.max_width
        self.y = (self.y + self.y_drops.pop()) % self.max_height
        return self.x, self.y

button_held_x = 1
button_held_y = 1

max_bright = 7

steps_per_interval = 15
sleep_time = 1 / steps_per_interval
num_of_petals = 10

petals = [
    Petal(
        random.randrange(WIDTH),
        random.randrange(HEIGHT),
        max_width=WIDTH,
        max_height=HEIGHT,
        steps_per_interval=steps_per_interval,
    )
    for _ in range(num_of_petals)
]

while True:
    for step in range(steps_per_interval):
        # A: Add a petal
        while scroll.is_pressed(scroll.BUTTON_A):
            petal = Petal(
                random.randrange(WIDTH),
                random.randrange(HEIGHT),
                max_width=WIDTH,
                max_height=HEIGHT,
                steps_per_interval=steps_per_interval,
            )
            petals.append(petal)

            scroll.clear()
            scroll.show_text(f"{len(petals)}P", max_bright, 0)
            scroll.show()
            time.sleep(0.2)

        # B: Remove a petal
        while scroll.is_pressed(scroll.BUTTON_B):
            if petals:
                petals.pop(0)

            scroll.clear()
            scroll.show_text(f"{len(petals)}P", max_bright, 0)
            scroll.show()
            time.sleep(0.2)

        # X: Brighter
        if scroll.is_pressed(scroll.BUTTON_X):
            max_bright = min(max_bright + button_held_x, 255)
            button_held_x = min(button_held_x + 1, 255)
            if max_bright >= 255:
                scroll.clear()
                scroll.show_text("MAX", 255, 0)
                scroll.show()
                time.sleep(0.5)
        else:
            button_held_x = 1

        # Y: Dimmer
        if scroll.is_pressed(scroll.BUTTON_Y):
            max_bright = max(max_bright - button_held_y, 0)
            button_held_y = min(button_held_y + 1, 255)
        else:
            button_held_y = 1

        scroll.clear()

        for petal in petals:
            points = petal.grid()
            for x, y, brightness in points:
                if not brightness:
                    continue

                try:
                    scroll.set_pixel(x, y, math.floor(max_bright * brightness))
                except ValueError as error:
                    print(x, y, brightness)
                    raise error

        scroll.show()
        time.sleep(sleep_time)

        for petal in petals:
            petal.walk()
