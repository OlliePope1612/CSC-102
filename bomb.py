#################################
# CSC 102 Defuse the Bomb Project
# Main program w/ Family Guy “icing”
#################################

import tkinter as tk
from tkinter import Toplevel, Label
from PIL import Image, ImageTk
from bomb_configs import *
from bomb_phases import *

# —————————————————————————————————————————————
# Full-screen image helper
# —————————————————————————————————————————————
img_window = None
img_photo  = None

def check_phases():
    global strikes_left, active_phases

    # sanity check
    assert None not in (keypad, toggles, wires, button), \
        "You must call setup_phases() before check_phases()!"

    # refresh labels once
    try:
        gui._ltimer["text"] = f"Time left: {timer}"
    except:
        pass
    try:
        gui._lkeypad["text"] = f"Keypad phase: {keypad}"
    except:
        pass
    try:
        gui._lwires["text"] = f"Wires phase: {wires}"
    except:
        pass
    try:
        gui._lbutton["text"] = f"Button phase: {button}"
    except:
        pass
    try:
        gui._ltoggles["text"] = f"Toggles phase: {toggles}"
    except:
        pass
    try:
        gui._lstrikes["text"] = f"Strikes left: {strikes_left}"
    except:
        pass

    # handle failures/defuses
    for phase in (keypad, toggles, wires, button):
        if phase is None:
            continue
        if phase._failed:
            strikes_left  -= 1
            active_phases -= 1
            phase._failed = False
        elif phase._defused:
            active_phases -= 1
            # leave phase._defused True so the label stays “DEFUSED”

    # continue or finish
    if strikes_left <= 0:
        gui.conclusion(success=False)
    elif active_phases <= 0:
        gui.conclusion(success=True)
    else:
        root.after(100, check_phases)

def show_image(path, hold_ms=2000):
    """Full-screen Toplevel that auto-closes after hold_ms."""
    global img_window, img_photo
    if img_window:
        try:
            img_window.destroy()
        except:
            pass

    img_window = Toplevel(root)
    img_window.attributes('-fullscreen', True)
    # load & scale
    w = root.winfo_screenwidth()
    h = root.winfo_screenheight()
    img = Image.open(path).resize((w, h), Image.LANCZOS)
    img_photo = ImageTk.PhotoImage(img)
    Label(img_window, image=img_photo).pack(fill='both', expand=True)

    # schedule auto-close
    root.after(hold_ms, img_window.destroy)

# —————————————————————————————————————————————
# Challenge & strike images (in phase order)
# —————————————————————————————————————————————
challenge_images = [
    "KEYPAD.jpeg",   # phase 0 = Keypad
    "WIRES.jpeg",    # phase 1 = Wires
    "TOGGLES.jpeg",  # phase 2 = Toggles
    "BUTTON.jpeg",   # phase 3 = Button
]
strike_images = [
    "STRIKE1.jpeg",
    "STRIKE2.jpeg",
    "STRIKE3.jpeg",
]

# —————————————————————————————————————————————
# Global state
# —————————————————————————————————————————————
strikes_left   = NUM_STRIKES
active_phases  = NUM_PHASES
handled_phases = set()     # keeps track of defused phases

# placeholders for phase objects
timer = keypad = wires = button = toggles = None

# —————————————————————————————————————————————
# Phase setup
# —————————————————————————————————————————————
def setup_phases():
    global strikes_left, active_phases, handled_phases
    global timer, keypad, wires, toggles, button

    strikes_left   = NUM_STRIKES
    active_phases  = NUM_PHASES
    handled_phases = set()

    # instantiate each phase
    tmr  = Timer(component_7seg, COUNTDOWN)
    kpd  = Keypad(component_keypad, keypad_target)
    wres = Wires(component_wires, wires_target)
    btn  = Button(
        component_button_state,
        component_button_rgb,
        button_target, button_color, tmr
    )
    tgl  = Toggles(component_toggles, toggles_target)

    # connect to GUI
    gui.setTimer(tmr)
    gui.setButton(btn)

    # start threads
    for p in (tmr, kpd, wres, btn, tgl):
        p.start()

    # expose globally for check_phases
    globals().update(
        timer=tmr,
        keypad=kpd,
        wires=wres,
        button=btn,
        toggles=tgl
    )

    # show first challenge
    show_image(challenge_images[0], hold_ms=1500)

# —————————————————————————————————————————————
# MAIN
# —————————————————————————————————————————————
if __name__ == '__main__':
    root = tk.Tk()
    gui  = Lcd(root)

    # immediately show your boot GUI
    gui.setup()

    # after GUI is ready, fire everything up
    root.after(200, setup_phases)
    root.after(300, check_phases)

    root.mainloop()
