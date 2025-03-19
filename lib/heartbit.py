from time import sleep
from adafruit_clue import clue
from adafruit_is31fl3731.scroll_phat_hd import ScrollPhatHD as Display


display = Display(clue._i2c)

def charge():
    frame_0 = """
    11011111101111101
    10011110101111011
    10111110001110001
    11111110101111011
    11111110111110111
    11111111111111111
    11111111111111111
    """
    frame_1 = """
    11111111111111111
    11111111111111111
    11111111111111111
    11111111111111111
    11111111111111111
    11111111111111111
    11111111111111111
    """

    display.frame(0, show=False)
    for i_row, row in enumerate(frame_0.split()):
        for i_column, column in enumerate(row):
            display.pixel(i_column, i_row, 0 if column == "0" else 100)
    display.frame(1, show=False)
    for i_row, row in enumerate(frame_1.split()):
        for i_column, column in enumerate(row):
            display.pixel(i_column, i_row, 0 if column == "0" else 100)

    while True:
        display.frame(0, show=True)
        sleep(1)
        display.frame(1, show=True)
        sleep(1)


def wave():
    sweep = [ 1, 2, 3, 4, 6, 8, 10, 15, 20, 30, 40, 60,
        60, 40, 30, 20, 15, 10, 8, 6, 4, 3, 2, 1, ]

    frame = 0

    display.blink(1000)
    while True:
        for incr in range(24):
            display.frame(frame, show=False)

            for row in range(display.height):
                for column in range(display.width):
                    # brightness = column * row
                    brightness = sweep[(row+column+incr) % 24]
                    display.pixel(column, row, brightness, blink=brightness == 60)
                    # sleep(0.1)

            display.frame(frame, show=True)
            frame = not frame


def pattern_to_tuples(pattern: str):
    """Return list of (row, column) coordinates of lit pixels.

    Pattern should be a grid of 0 or 1 characters.

        00000000000000000
        00000001010000000
        00000001010000000
        00000000000000000
        00000001010000000
        00000000100000000
        00000000000000000

    """
    coordinates = []
    for row_i, row in enumerate(pattern.split()):
        for column_i, column in enumerate(row):
            if column == "1":
                coordinates.append((row_i, column_i))
    return coordinates

def choose_brightness():
    brightness = 10
    step = 5

    pattern_plus = pattern_to_tuples("""
        00000000000000000
        00000000000000000
        00000000100000000
        00000001110000000
        00000000100000000
        00000000000000000
        00000000000000000
    """)
    # pattern_plus = ((2,9), (3,8), (3,9), (3,10), (4,9))
    pattern_heart = pattern_to_tuples("""
        00000000000000000
        00000001010000000
        00000011111000000
        00000011111000000
        00000001110000000
        00000000100000000
        00000000000000000
    """)
    pattern = pattern_heart

    transition_frames = (
        pattern_to_tuples("""
        11111111111111111
        11111111111111111
        11111111111111111
        11111111111111111
        11111111111111111
        11111111111111111
        11111111111111111
        """),
        pattern_to_tuples("""
        00000000000000000
        00000000000000000
        00000000100000000
        00000001110000000
        00000000100000000
        00000000000000000
        00000000000000000
        """),
        pattern_to_tuples("""
        00000000000000000
        00000001110000000
        00000011111000000
        00000011111000000
        00000011111000000
        00000001110000000
        00000000000000000
        """),
        pattern_to_tuples("""
        00000011111000000
        00000111111100000
        00001111111110000
        00001111111110000
        00001111111110000
        00000111111100000
        00000011111000000
        """),
        pattern_to_tuples("""
        00001111111110000
        00011111111111000
        00111111111111100
        00111111111111100
        00111111111111100
        00011111111111000
        00001111111110000
        """),
        pattern_to_tuples("""
        00111111111111100
        01111111111111110
        11111111111111111
        11111111111111111
        11111111111111111
        01111111111111110
        00111111111111100
        """),
        pattern_to_tuples("""
        11111111111111111
        11111111111111111
        11111111111111111
        11111111111111111
        11111111111111111
        11111111111111111
        11111111111111111
        """),
    )

    def transition(old_brightness=0, brightness=0):
        # print(f"Transition to {old_brightness} -> {brightness}")

        step = (brightness - old_brightness) // 5
        current_brightness = old_brightness + step
        # steps = tuple(range(old_brightness+step, brightness+1, step))

        for frame, transition_frame in enumerate(transition_frames[1:], start=1):
            # print(f"{frame=} {current_brightness=}")
            display.frame(frame, show=False)
            display.fill(old_brightness, frame)

            for row, column in transition_frame:
                display.pixel(column, row, current_brightness)
            # current_brightness = max(min(current_brightness + step, 255), 0)
            current_brightness = brightness

        for frame in range(1, 7):
            sleep(0.05)
            display.frame(frame)

        display.frame(0, show=False)
        display.fill(brightness)
        # print(f"{brightness=}")

    def button_held(pressed_func, brightness=0, brightness_step=0):
        _step = brightness_step

        while pressed_func():
            change = brightness + _step
            brightness = min(max(change, 0), 255)

            display.frame(0, show=False)
            for row, column in pattern:
                display.pixel(column, row, brightness)
            display.frame(0, show=True)

            _step += brightness_step
            sleep(0.1)

        return brightness

    display.fill(brightness)

    while True:
        old_brightness = brightness

        brightness = button_held(lambda: clue.button_a, brightness=brightness, brightness_step=-step)
        brightness = button_held(lambda: clue.button_b, brightness=brightness, brightness_step=step)

        if old_brightness != brightness:
            transition(old_brightness=old_brightness, brightness=brightness)

        sleep(0.3)

choose_brightness()
