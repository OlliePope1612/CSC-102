#################################
# CSC 102 Defuse the Bomb Project
# Configuration file – Day 5 Hardware Integration
# Team:
#################################

# Detect environment: real Raspberry Pi vs. mock (macOS) mode
try:
    import board, busio, digitalio
    from adafruit_ht16k33.segments import Seg7x4
    from digitalio import DigitalInOut, Direction, Pull
    from adafruit_matrixkeypad import Matrix_Keypad
    RPi = True
except ImportError:
    RPi = True

# Enable debug prints and mock modules only when not on the Pi
debug_mode = not RPi
DEBUG = debug_mode
ANIMATE = True        		# animate the LCD boot text?
SHOW_BUTTONS = True   		# show Pause/Quit buttons in GUI (only matters in mock)
COUNTDOWN = 300       		# initial countdown (seconds)
NUM_STRIKES = 5       		# allowed strikes before explosion
NUM_PHASES = 5        		# total phases: Timer, Keypad, Wires, Button, Toggles
STAR_CLEARS_PASS = True		# allows star key to clear passcode

# Base imports used in both modes
from random import randint, shuffle, choice
from string import ascii_uppercase

# Inject mock modules when in debug mode (macOS)
if DEBUG:
    import sys, types
    mock_modules = ["board", "digitalio", "busio", "adafruit_character_lcd"]
    for mod in mock_modules:
        sys.modules[mod] = types.ModuleType(mod)

#################################
# setup the electronic components
#################################
if RPi:
    # 7‐segment display over I2C
    i2c = busio.I2C(board.SCL, board.SDA)
    component_7seg = Seg7x4(i2c)
    component_7seg.brightness = 0.5

    # matrix keypad
    keypad_cols = [DigitalInOut(i) for i in (board.D10, board.D9, board.D11)]
    keypad_rows = [DigitalInOut(i) for i in (board.D5, board.D6, board.D13, board.D19)]
    keypad_keys = ((1,2,3), (4,5,6), (7,8,9), ("*",0,"#"))
    component_keypad = Matrix_Keypad(keypad_rows, keypad_cols, keypad_keys)

    # jumper wires
    component_wires = [DigitalInOut(i) for i in (board.D14, board.D15, board.D18, board.D23, board.D24)]
    for pin in component_wires:
        pin.direction = Direction.INPUT
        pin.pull = Pull.DOWN

    # pushbutton (state + RGB)
    component_button_state = DigitalInOut(board.D4)
    component_button_state.direction = Direction.INPUT
    component_button_state.pull = Pull.DOWN
    component_button_RGB = [DigitalInOut(i) for i in (board.D17, board.D27, board.D22)]
    for pin in component_button_RGB:
        pin.direction = Direction.OUTPUT
        pin.value = True

    # toggle switches (3-pin configuration)
    component_toggles = [DigitalInOut(i) for i in (board.D12, board.D16, board.D20, board.D21)]
    for pin in component_toggles:
        pin.direction = Direction.INPUT
        pin.pull    = Pull.DOWN

else:
    # mock hardware components for macOS debug
    class MockSeg7x4:
        def __init__(self): self.blink_rate = 0
        def print(self, s): pass
        def fill(self, v):    pass

    class MockKeypad:
        def __init__(self): self.pressed_keys = []

    class MockWire:
        def __init__(self, idx): self._idx, self._cut = idx, False
        def is_cut(self):        return self._cut
        def cut(self):           self._cut = True

    class MockDigitalInOut:
        def __init__(self): self.value = False
        def read(self):       return self.value

    class MockTogglePin:
        def __init__(self): self.value = False
        def read(self):       return self.value

    component_7seg         = MockSeg7x4()
    component_keypad       = MockKeypad()
    component_wires        = [MockWire(i) for i in range(5)]
    component_button_state = MockDigitalInOut()
    component_button_RGB   = [MockDigitalInOut() for _ in range(3)]
    component_toggles      = [MockTogglePin() for _ in range(4)]

###########
# helper functions: serial generation & keypad cipher
###########

def genSerial():
    # digits for toggles sum
    serial_digits = []
    toggle_value  = randint(1, 7)  # restrict to 3-bit range 1..7
    while len(serial_digits) < 3 or toggle_value - sum(serial_digits) > 0:
        d = randint(0, min(9, toggle_value - sum(serial_digits)))
        serial_digits.append(d)

    # wires pattern: pick 3 of 5 bits
    jumper_indexes = [0]*5
    while sum(jumper_indexes) < 3:
        jumper_indexes[randint(0, 4)] = 1
    jumper_value   = int("".join(str(n) for n in jumper_indexes), 2)
    jumper_letters = [ chr(i+65) for i,n in enumerate(jumper_indexes) if n == 1]

    # build & shuffle serial
    serial = [str(d) for d in serial_digits] + jumper_letters
    shuffle(serial)
    serial += [ choice([chr(n) for n in range(70,91)]) ]
    return "".join(serial), toggle_value, jumper_value


def genKeypadCombination():
    def encrypt(keyword, rot):
        return "".join(chr((ord(c)-65+rot)%26+65) for c in keyword)
    def digits(passphrase):
        keys = [None, None, "ABC","DEF","GHI","JKL","MNO","PRS","TUV","WXY"]
        combo = ""
        for c in passphrase:
            for i,k in enumerate(keys):
                if k and c in k:
                    combo += str(i)
        return combo

    keywords = {"BANDIT":"RIVER","BUCKLE":"FADED","CANOPY":"FOXES",
                "DEBATE":"THROW","FIERCE":"TRICK","GIFTED":"CYCLE",
                "IMPACT":"STOLE","LONELY":"TOADY","MIGHTY":"ALOOF",
                "NATURE":"CARVE","REBORN":"CLIMB","RECALL":"FEIGN",
                "SYSTEM":"LEAVE","TAKING":"SPINY","WIDELY":"BOUND",
                "ZAGGED":"YACHT"}
    rot        = randint(1,25)
    keyword, passphrase = choice(list(keywords.items()))
    cipher_keyword = encrypt(keyword, rot)
    combination    = digits(passphrase)
    return keyword, cipher_keyword, rot, combination, passphrase

###############################
# generate bomb specifics
###############################
serial, toggles_target, wires_target = genSerial()
keyword, cipher_keyword, rot, keypad_target, passphrase = genKeypadCombination()
button_color = None
button_target = None

if DEBUG:
    print(f"Serial number: {serial}")
    print(f"Toggles target: {bin(toggles_target)[2:].zfill(len(component_toggles))}/{toggles_target}")
    print(f"Wires target:   {bin(wires_target)[2:].zfill(len(component_wires))}/{wires_target}")
    print(f"Keypad target:  {keypad_target}/{passphrase}/{cipher_keyword}(rot={rot})")
    print(f"Button target:  {button_target}")

# bootup splash text
boot_text = (
    "Booting...\n\x00\x00"
    "*Kernel v3.1.4-159 loaded.\n"
    "Initializing subsystems...\n\x00"
    "*System model: 102BOMBv4.2\n"
    f"*Serial number: {serial}\n"
    "Encrypting keypad...\n\x00"
    f"*Keyword: {cipher_keyword}; key: {rot}\n"
    "*" + " ".join(ascii_uppercase) + "\n"
    "*" + " ".join(str(n%10) for n in range(26)) + "\n"
    "Rendering phases...\x00"
)
from bomb_phases import Keypad, Wires, Toggles
import random

# === FAMILY GUY THEME: Randomized bomb targets ===

# Generate random target values
correct_code = str(random.randint(10000, 99999))  # 5-digit code for keypad
correct_wire = random.choice(["orange", "yellow", "blue", "green", "purple"])  # unplug wire
correct_switch_pattern = "".join([str(random.choice([0, 1])) for _ in range(4)])  # e.g., "1010"

# Show debug values if needed
if DEBUG:
    print("\n[DEBUG MODE] Bomb Configuration:")
    print(f"Keypad code: {correct_code}")
    print(f"Correct wire: {correct_wire}")
    print(f"Switch pattern: {correct_switch_pattern}\n")

# === Component-phase mapping ===
phase_defs = [
    (component_keypad, Keypad, correct_code),
    (component_wires,  Wires,  correct_wire),
    (component_toggles, Toggles, correct_switch_pattern)
]

