#################################
# CSC 102 Defuse the Bomb Project
# Configuration file – Day 5 Hardware Integration (Family Guy themed)
#################################

# Detect environment: real Raspberry Pi vs. mock (macOS) mode
try:
    import board, busio, digitalio
    from adafruit_ht16k33.segments import Seg7x4
    from digitalio import DigitalInOut, Direction, Pull
    from adafruit_matrixkeypad import Matrix_Keypad
    RPi = True
except ImportError:
    RPi = False

# Debug and animation settings
DEBUG = not RPi           # verbose debug prints when not on Pi
ANIMATE = True            # animate the LCD boot text
SHOW_BUTTONS = True       # show Pause/Quit buttons in GUI

# Bombgame constants
COUNTDOWN = 300           # initial countdown (seconds)
NUM_STRIKES = 5           # allowed strikes before explosion
NUM_PHASES = 5            # total phases: Timer, Keypad, Wires, Button, Toggles
STAR_CLEARS_PASS = True   # allows '*' to clear keypad input

# Standard imports
from random import shuffle
from string import ascii_uppercase

# Inject mock modules when in debug mode (macOS)
if DEBUG:
    import sys, types
    for mod in ["board", "digitalio", "busio", "adafruit_ht16k33.segments", "adafruit_matrixkeypad"]:
        sys.modules[mod] = types.ModuleType(mod)

#################################
# setup the electronic components
#################################
if RPi:
    # 7-segment display over I2C
    i2c = busio.I2C(board.SCL, board.SDA)
    component_7seg = Seg7x4(i2c)
    component_7seg.brightness = 0.5

    # matrix keypad
    keypad_cols = [DigitalInOut(pin) for pin in (board.D10, board.D9, board.D11)]
    keypad_rows = [DigitalInOut(pin) for pin in (board.D5, board.D6, board.D13, board.D19)]
    component_keypad = Matrix_Keypad(keypad_rows, keypad_cols, ((1,2,3),(4,5,6),(7,8,9),("*",0,"#")))

    # jumper wires
    component_wires = [DigitalInOut(pin) for pin in (board.D14, board.D15, board.D18, board.D23, board.D24)]
    for pin in component_wires:
        pin.direction = Direction.INPUT
        pin.pull = Pull.DOWN

    # pushbutton (state + RGB)
    component_button_state = DigitalInOut(board.D4)
    component_button_state.direction = Direction.INPUT
    component_button_state.pull = Pull.DOWN
    component_button_RGB = [DigitalInOut(pin) for pin in (board.D17, board.D27, board.D22)]
    for pin in component_button_RGB:
        pin.direction = Direction.OUTPUT
        pin.value = True

    # toggle switches
    component_toggles = [DigitalInOut(pin) for pin in (board.D12, board.D16, board.D20, board.D21)]
    for pin in component_toggles:
        pin.direction = Direction.INPUT
        pin.pull = Pull.DOWN

else:
    # mock hardware for macOS debug
    class MockSeg7x4:
        def __init__(self): self.blink_rate = 0
        def print(self, s): pass
        def fill(self, v): pass

    class MockKeypad:
        def __init__(self): self.pressed_keys = []

    class MockWire:
        def __init__(self, idx): self._idx, self._cut = idx, False
        def is_cut(self): return self._cut
        def cut(self): self._cut = True

    class MockDigitalInOut:
        def __init__(self): self.value = False
        def read(self): return self.value

    class MockTogglePin(MockDigitalInOut):
        pass

    component_7seg = MockSeg7x4()
    component_keypad = MockKeypad()
    component_wires = [MockWire(i) for i in range(5)]
    component_button_state = MockDigitalInOut()
    component_button_RGB = [MockDigitalInOut() for _ in range(3)]
    component_toggles = [MockTogglePin() for _ in range(4)]

###########
# Family Guy Themed Quotes
###########
quagmire_lines = [
    "Giggity! This keypad's hotter than Lois!",
    "I'd tap that... code.",
    "Giggity giggity goo!"
]

joe_lines = [
    "MY WHEELCHAIR'S DEAD!",
    "HELP! PUSH ME CLOSER!",
    "PETER, YOU'RE OUR ONLY HOPE!"
]

cleveland_lines = [
    "No no no no NO!",
    "Oh, that's not good...",
    "I'm getting outta here!"
]

###########
# Hardcoded Bomb Setup (Scripted)
###########
# Keypad phase code
keypad_target = "69420"
# Wires phase: only the middle (3rd) wire must be cut
wires_target = int("00100", 2)
# Toggles phase pattern: ON, OFF, ON, ON
toggles_target = int("1011", 2)
# Serial number for boot text
serial = "DRUNKNCLAM"

# Button logic is handled dynamically in the Button class; button_target unused here
button_target = None

# bootup splash text
boot_text = (
    "Booting...\n\x00\x00"
    "*Kernel v3.1.4-159 loaded.\n"
    "Initializing subsystems...\n\x00"
    "*System model: 102BOMBv4.2\n"
    f"*Serial number: {serial}\n"
    "Encrypting keypad...\n\x00"
    f"*Keyword: CLAM; key: 6\n"
    "*" + " ".join(ascii_uppercase) + "\n"
    "*" + " ".join(str(n%10) for n in range(26)) + "\n"
    "Rendering phases...\x00"
)

# Debug print of configuration
if DEBUG:
    print("[DEBUG MODE] Bomb Configuration:")
    print(f"Keypad code: {keypad_target}")
    print(f"Wire pattern: {bin(wires_target)[2:].zfill(5)}")
    print(f"Toggle pattern: {bin(toggles_target)[2:].zfill(4)}")
    print(f"Serial: {serial}")
