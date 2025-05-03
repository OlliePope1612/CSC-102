#################################
# CSC 102 Defuse the Bomb Project
# Main program – Day 3 GUI integration
#################################

from tkinter import Tk
from bomb_configs import *        # brings in component_7seg, component_keypad, etc., plus COUNTDOWN, targets, RPi
from bomb_phases import *         # brings in Timer, Keypad, Wires, Button, Toggles, Lcd

# Dialogue for family guy
dialogues = {
    'intro':   "Stewie: At long last, Quahog will be no more! Brian: Oh dear, we must act fast!",
    'Keypad':  "Brian: Nice job cracking the code! Now sever the correct circuits.",
    'Wires':   "Brian: Wires cut! Next flip the family crests.",
    'Toggles': "Brian: Toggles set! Now press the button at the right time.",
    'Button':  "Brian: Button done! Final override to finish this.",
    'Defused': "Brian: You saved Quahog! Hooray."
}

handled_phases = set()
###########
# Helper functions
###########

def check_phases():
    global strikes_left, active_phases, handled_phases

    # 1) Refresh the labels
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

    # 2) Handle each phase exactly once
    for phase in (keypad, wires, button, toggles):
        if phase in handled_phases:
            continue

        if phase._failed:
            strikes_left  -= 1
            active_phases -= 1
            handled_phases.add(phase)

        elif phase._defused:
            active_phases -= 1
            handled_phases.add(phase)

    # 3) End‐of‐game?
    if strikes_left <= 0:
        gui.conclusion(success=False)
    elif active_phases <= 0:
        gui.conclusion(success=True)
    else:
        gui.after(100, check_phases)
        
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

# generates the bootup sequence on the LCD
def bootup(n=0):
    if (not ANIMATE or n == len(boot_text)):
        # if (not ANIMATE):
        #     gui._lscroll["text"] = boot_text.replace("\x00", "")
        gui.setup()
    else:
        # append the next character (skip the pause-marker \x00)
        if (boot_text[n] != "\x00"):
            gui._lscroll["text"] += boot_text[n]
        # schedule the next scroll
        delay = 25 if boot_text[n] != "\x00" else 750
        gui.after(delay, bootup, n + 1)

###########
# MAIN
###########

window = Tk()
gui = Lcd(window)

gui.after(1000, bootup)
# after boot scroll finishes, kick off the real GUI & logic
boot_duration = 1000 + len(boot_text) * 50
gui.after(boot_duration, start_game)

window.mainloop()
