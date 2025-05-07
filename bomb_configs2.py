#################################
# CSC 102 Defuse the Bomb Project
# Configuration file – Day 5 Hardware Integration
#################################

# constants
DEBUG = False        # enable verbose debug prints
ANIMATE = True       # animate the LCD boot text?
SHOW_BUTTONS = False # show Pause/Quit buttons on GUI?
COUNTDOWN = 300      # initial countdown timer (seconds)
NUM_STRIKES = 5      # allowed failures before explosion
NUM_PHASES = 4       # number of interactive phases (Keypad, Wires, Toggles, Button)

# detect environment: real Raspberry Pi vs mock mode
try:
    import board, busio
    from adafruit_ht16k33.segments import Seg7x4
    from digitalio import DigitalInOut, Direction, Pull
    from adafruit_matrixkeypad import Matrix_Keypad
    RPi = True
except ImportError:
    RPi = False

# hardware component placeholders
if RPi:
    # 7‐segment display over I2C
    i2c = busio.I2C(board.SCL, board.SDA)
    component_7seg = Seg7x4(i2c)
    component_7seg.brightness = 0.5

    # matrix keypad (4×3)
    cols = [DigitalInOut(pin) for pin in (board.D10, board.D9, board.D11)]
    rows = [DigitalInOut(pin) for pin in (board.D5, board.D6, board.D13, board.D19)]
    component_keypad = Matrix_Keypad(rows, cols, ((1,2,3),(4,5,6),(7,8,9),('*',0,'#')))

    # jumper wires (5 inputs)
    component_wires = [DigitalInOut(pin) for pin in (board.D14, board.D15, board.D18, board.D23, board.D24)]
    for w in component_wires:
        w.direction = Direction.INPUT
        w.pull = Pull.DOWN

    # pushbutton + RGB LEDs
    btn = DigitalInOut(board.D4)
    btn.direction = Direction.INPUT
    btn.pull = Pull.DOWN
    component_button_state = btn
    component_button_RGB = [DigitalInOut(pin) for pin in (board.D17, board.D27, board.D22)]
    for led in component_button_RGB:
        led.direction = Direction.OUTPUT
        led.value = False

    # toggle switches (4 inputs)
    component_toggles = [DigitalInOut(pin) for pin in (board.D12, board.D16, board.D20, board.D21)]
    for t in component_toggles:
        t.direction = Direction.INPUT
        t.pull = Pull.DOWN
else:
    # mock hardware for development
    class MockSeg7x4:
        def __init__(self): pass
        def print(self, s): pass
        def fill(self, v): pass
    component_7seg = MockSeg7x4()

    class MockKeypad:
        def __init__(self): self.pressed_keys = []
    component_keypad = MockKeypad()

    class MockWire:
        def __init__(self): self.cut = False
        def is_cut(self): return self.cut
    component_wires = [MockWire() for _ in range(5)]

    class MockPin:
        def __init__(self): self.value = False
        def read(self): return self.value
    component_toggles = [MockPin() for _ in range(4)]
    component_button_state = MockPin()
    component_button_RGB = [MockPin() for _ in range(3)]

# helper: serial & keypad generation
import random
from random import randint, shuffle, choice
from string import ascii_uppercase

correct_code = [1999, 135, 1235, 31415]
correct_switch_pattern = [1010, 1010, 1011, 1100]
correct_wire = [10101, 10000, 10001, 10100]
amount_of_presses = [5, 7, 15, 8] # button_target
BUTTON_MAX_TIME = [7, 8, 10, 9]
button_color = 'R'

keypad_images = ["KEYPAD.jpeg", "KEYPAD2.jpeg", "KEYPAD3.jpeg", "KEYPAD4.jpeg"]
wires_images  = ["WIRES.jpeg",  "WIRES2.jpeg",  "WIRES3.jpeg",  "WIRES4.jpeg"]
toggles_images= ["TOGGLES.jpeg", "TOGGLES2.jpeg", "TOGGLES3.jpeg", "TOGGLES4.jpeg"]
button_images = ["BUTTON.jpeg", "BUTTON2.jpeg", "BUTTON3.jpeg", "BUTTON4.jpeg"]


keypad_audio = ["KEYPAD1.wav", "KEYPAD2.wav", "KEYPAD3.wav", "KEYPAD4.wav"]
wires_audio = ["WIRES.wav", "ONETHOUSAND.wav", "WIRES3.wav", "WIRES4.wav"]
toggles_audio = ["TOGGLES.wav", "TOGGLES2.wav", "TOGGLES3.wav", "TOGGLES4.wav"]
button_audio = ["FIVETIMES.wav", "SEVENTIMES.wav", "FIFTEENTIMES.wav", "EIGHTTIMES.wav"]
strike_audio = ["STRIKE4.wav", "STRIKE3.wav", "STRIKE2.wav", "STRIKE1.wav"]
def genSerial():
    # sum-of-digits defines toggles target (1..15)
    serial_digits = []
    toggle_value = randint(1,15)
    while len(serial_digits)<3 or toggle_value - sum(serial_digits) > 0:
        d = randint(0, min(9, toggle_value - sum(serial_digits)))
        serial_digits.append(d)
    # jumper pattern: pick 3 of 5
    jumper_bits = [0]*5
    while sum(jumper_bits)<3:
        jumper_bits[randint(0,4)] = 1
    jumper_value = int("".join(str(b) for b in jumper_bits), 2)
    jumper_letters = [chr(i+65) for i,b in enumerate(jumper_bits) if b]
    # build serial
    parts = [str(d) for d in serial_digits] + jumper_letters
    shuffle(parts)
    parts += [choice([chr(n) for n in range(70,91)])]
    return "".join(parts), toggle_value, jumper_value

def genKeypadCombination():
    # rotation cipher
    def encrypt(keyword, rot):
        return "".join(chr((ord(c)-65+rot)%26+65) for c in keyword)
    # map letters to digits
    def digits(passph):
        keys = [None, None,"ABC","DEF","GHI","JKL","MNO","PRS","TUV","WXY"]
        combo = ""
        for c in passph:
            for i,k in enumerate(keys):
                if k and c in k:
                    combo+=str(i)
        return combo
    tbl = {"BANDIT":"RIVER","BUCKLE":"FADED","CANOPY":"FOXES",
           "DEBATE":"THROW","FIERCE":"TRICK","GIFTED":"CYCLE",
           "IMPACT":"STOLE","LONELY":"TOADY","MIGHTY":"ALOOF",
           "NATURE":"CARVE","REBORN":"CLIMB","RECALL":"FEIGN",
           "SYSTEM":"LEAVE","TAKING":"SPINY","WIDELY":"BOUND",
           "ZAGGED":"YACHT"}
    rot = randint(1,25)
    keyword, passph = choice(list(tbl.items()))
    cipher = encrypt(keyword, rot)
    combo = digits(passph)
    return keyword, cipher, rot, combo, passph

# generate all targets
serial, toggles_target, wires_target = genSerial()
keyword, cipher_keyword, rot, keypad_target, passphrase = genKeypadCombination()

# boot text for LCD
boot_text = (
    "Booting...\n" +
    "*Serial#: " + serial + "\n" +
    "*Keyword: " + cipher_keyword + "; key=" + str(rot) + "\n" +
    "*Pattern: " + format(wires_target,'05b') + " (wires)\n" +
    "*Pattern: " + format(toggles_target,'04b') + " (toggles)\n"
)


# Debug output
if DEBUG:
    print("=== DEBUG CONFIG ===")
    print(f"Serial number     = {serial}")
    print(f"Keypad target     = {keypad_target} ({passphrase})")
    print(f"Wires target      = {format(wires_target,'05b')}")
    print(f"Toggles target    = {format(toggles_target,'04b')}")
    print(f"Button presses    = {button_target} on {button_color} LED")
