"""Hardware setup and puzzle configuration for Defuse the Bomb.

Set RPi = True only on the Raspberry Pi with the listed components connected.
Keep RPi = False for Windows development and GUI testing.
"""
from random import choice

DEBUG = False
RPi = False
SHOW_BUTTONS = False
COUNTDOWN = 300
NUM_STRIKES = 5
NUM_PHASES = 4
NUM_MATH_QUESTIONS = 2
TRIVIA_PENALTY = 5

if RPi:
    import board
    from adafruit_ht16k33.segments import Seg7x4
    from digitalio import DigitalInOut, Direction, Pull
    from adafruit_matrixkeypad import Matrix_Keypad

    i2c = board.I2C()
    component_7seg = Seg7x4(i2c)
    component_7seg.brightness = 0.5

    keypad_cols = [DigitalInOut(pin) for pin in (board.D10, board.D9, board.D11)]
    keypad_rows = [DigitalInOut(pin) for pin in (board.D5, board.D6, board.D13, board.D19)]
    keypad_keys = ((1, 2, 3), (4, 5, 6), (7, 8, 9), ("*", 0, "#"))
    component_keypad = Matrix_Keypad(keypad_rows, keypad_cols, keypad_keys)

    component_wires = [
        DigitalInOut(pin) for pin in
        (board.D14, board.D15, board.D18, board.D23, board.D24)
    ]
    for pin in component_wires:
        pin.direction = Direction.INPUT
        pin.pull = Pull.DOWN

    component_button_state = DigitalInOut(board.D4)
    component_button_state.direction = Direction.INPUT
    component_button_state.pull = Pull.DOWN
    component_button_RGB = [
        DigitalInOut(pin) for pin in (board.D17, board.D27, board.D22)
    ]
    for pin in component_button_RGB:
        pin.direction = Direction.OUTPUT
        pin.value = True

    component_toggles = [
        DigitalInOut(pin) for pin in (board.D12, board.D16, board.D20, board.D21)
    ]
    for pin in component_toggles:
        pin.direction = Direction.INPUT
        pin.pull = Pull.DOWN


def genSerial():
    return "B026DES"


def genTogglesTarget():
    return 12  # binary 1100


def genWiresTarget():
    return 4  # binary 00100


def genKeypadTarget():
    return "235"


def genMathQuestions():
    return [
        {
            "question": (
                "Q1: Select the 3 smallest prime numbers.\n"
                "Enter them with no spaces (e.g., 235)."
            ),
            "answer": "235",
        },
        {"question": "Q2: What is 12 x 11?", "answer": "132"},
    ]


serial = genSerial()
toggles_target = genTogglesTarget()
wires_target = genWiresTarget()
keypad_target = genKeypadTarget()
button_color = choice(["R", "G", "B"])


def genButtonTarget():
    digits = [character for character in serial if character.isdigit()]
    if button_color == "G":
        return digits[0]
    if button_color == "B":
        return digits[-1]
    return None


button_target = genButtonTarget()
math_questions = genMathQuestions()
trivia_questions = math_questions
trivia_question = math_questions[0]["question"]

boot_text = (
    "Welcome to Mathematical Meltdown!\n"
    "You have 5 minutes to defuse the bomb. Good luck!\n"
    "Keypad: enter the three smallest prime numbers.\n"
    "Wires: set the binary pattern for decimal 4.\n"
    "Toggles: set the binary pattern 1100.\n"
    "Button: complete five press-and-release cycles.\n"
)
