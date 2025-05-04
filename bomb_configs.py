"""
bomb_configs.py
Simple configuration & hardware‐abstraction for the bomb project.
"""

import random

# Detect whether we’re on a real Raspberry Pi or not
try:
    import board, busio, digitalio
    from adafruit_ht16k33.segments import Seg7x4
    from adafruit_matrixkeypad import Matrix_Keypad
    RPi = True
except ImportError:
    RPi = False

# Gameplay constants
COUNTDOWN    = 120    # seconds
NUM_STRIKES  = 3
NUM_PHASES   = 4

# Hardware components (real or mock)
if RPi:
    # 7-segment display
    i2c = busio.I2C(board.SCL, board.SDA)
    component_7seg = Seg7x4(i2c)
    component_7seg.brightness = 0.5

    # matrix keypad
    cols = [digitalio.DigitalInOut(pin) for pin in (board.D10, board.D9, board.D11)]
    rows = [digitalio.DigitalInOut(pin) for pin in (board.D5, board.D6, board.D13, board.D19)]
    keys = ((1,2,3),(4,5,6),(7,8,9),('*',0,'#'))
    component_keypad = Matrix_Keypad(rows, cols, keys)

    # 5 jumper wires
    component_wires = [digitalio.DigitalInOut(pin) for pin in (board.D14, board.D15, board.D18, board.D23, board.D24)]
    for p in component_wires:
        p.direction = digitalio.Direction.INPUT
        p.pull      = digitalio.Pull.DOWN

    # pushbutton state + RGB LED
    component_button_state = digitalio.DigitalInOut(board.D4)
    component_button_state.direction = digitalio.Direction.INPUT
    component_button_state.pull      = digitalio.Pull.DOWN
    component_button_rgb = [digitalio.DigitalInOut(pin) for pin in (board.D17, board.D27, board.D22)]
    for p in component_button_rgb:
        p.direction = digitalio.Direction.OUTPUT
        p.value     = True

    # 4 toggle switches
    component_toggles = [digitalio.DigitalInOut(pin) for pin in (board.D12, board.D16, board.D20, board.D21)]
    for p in component_toggles:
        p.direction = digitalio.Direction.INPUT
        p.pull      = digitalio.Pull.DOWN

else:
    # Mock classes for macOS testing
    class Mock7Seg:
        def __init__(self): self.blink_rate = 0
        def print(self, s): pass
        def fill(self, v):    pass

    class MockKeypad:
        def __init__(self): self.pressed_keys = []

    class MockWire:
        def __init__(self, idx): self._cut = False
        def is_cut(self):        return self._cut
        def cut(self):           self._cut = True

    class MockPin:
        def __init__(self): self.value = False
        def read(self):       return self.value

    component_7seg         = Mock7Seg()
    component_keypad       = MockKeypad()
    component_wires        = [MockWire(i) for i in range(5)]
    component_button_state = MockPin()
    component_button_rgb   = [MockPin() for _ in range(3)]
    component_toggles      = [MockPin() for _ in range(4)]

# **STATIC** targets for now (replace with genSerial/genKeypad for randomness)
toggles_target = '1010'
wires_target   = '11001'
keypad_target  = '1234'
button_target  = None   # if None, button‐puzzle is “release on a correct timer digit”
