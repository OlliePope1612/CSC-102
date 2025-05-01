from bomb_phases import Wires
from bomb_configs import wires_target
import time

class MockWire:
    def __init__(self, idx):
        self._idx, self._cut = idx, False
    def is_cut(self):
        return self._cut
    def cut(self):
        self._cut = True

bits  = bin(wires_target)[2:].zfill(5)
wires = [MockWire(i) for i in range(len(bits))]
wir   = Wires(wires, bits)
wir.start()

for idx in map(int, bits):
    wires[idx].cut()
    time.sleep(0.05)

wir.join()
print("Wires defused?", wir._defused, "Failed?", wir._failed)
