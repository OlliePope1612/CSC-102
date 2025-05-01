#################################
# CSC 102 Defuse the Bomb Project
# Main program – Day 3 GUI integration
#################################

from tkinter import Tk
from bomb_configs import *        # brings in component_7seg, component_keypad, etc., plus COUNTDOWN, targets, RPi
from bomb_phases import *         # brings in Timer, Keypad, Wires, Button, Toggles, Lcd

###########
# Helper functions
###########

def setup_phases():
    global timer, keypad, wires, button, toggles, strikes_left, active_phases

    strikes_left  = NUM_STRIKES
    active_phases = NUM_PHASES

    timer   = Timer(component_7seg, COUNTDOWN)
    keypad  = Keypad(component_keypad, str(keypad_target))
    wires   = Wires(component_wires, bin(wires_target)[2:].zfill(5))
    button  = Button(component_button_state,
                     component_button_RGB,
                     button_target, button_color, timer)
    toggles = Toggles(component_toggles, bin(toggles_target)[2:].zfill(4))

    gui.setTimer(timer)
    gui.setButton(button)

    for phase in (timer, keypad, wires, button, toggles):
        phase.start()


def check_phases():
    global strikes_left, active_phases

    while active_phases > 0 and strikes_left > 0:
        # update labels; wrap each in try/except so we don’t crash after conclusion()
        try: gui._ltimer[  "text"] = f"Time left: {timer}"
        except: pass
        try: gui._lkeypad["text"] = f"Keypad phase: {keypad}"
        except: pass
        try: gui._lwires[  "text"] = f"Wires phase: {wires}"
        except: pass
        try: gui._lbutton["text"] = f"Button phase: {button}"
        except: pass
        try: gui._ltoggles["text"] = f"Toggles phase: {toggles}"
        except: pass
        try: gui._lstrikes["text"] = f"Strikes left: {strikes_left}"
        except: pass

        for phase in (keypad, wires, button, toggles):
            if phase._failed:
                strikes_left  -= 1
                active_phases -= 1
                phase._failed = False
            if phase._defused:
                active_phases -= 1
                phase._defused = False

        gui.update()
        gui.after(100)

    gui.conclusion(success=(strikes_left > 0))


def start_game():
    # Build the live‐game GUI
    gui.setup()

    # Only on a real Pi do we spin up the hardware threads;
    # on macOS this just leaves the labels in place (you could
    # manually poke them via the REPL if needed)
    if RPi:
        setup_phases()
        window.after(100, check_phases)


###########
# MAIN
###########

window = Tk()
gui = Lcd(window)

# after boot scroll finishes, kick off the real GUI & logic
boot_duration = 1000 + len(boot_text) * 50
gui.after(boot_duration, start_game)

window.mainloop()
