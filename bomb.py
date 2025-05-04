# bomb.py
#################################
# CSC 102 Defuse the Bomb Project
# Main program w/ Family Guy “icing”
#################################

import tkinter as tk
from tkinter import Toplevel, Label
from PIL import Image, ImageTk
from bomb_configs import *                 # hardware components & constants
from bomb_phases import Timer, Keypad, Wires, Button, Toggles, Lcd

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
    try: gui._ltimer["text"]   = f"Time left: {timer}"
    except: pass
    try: gui._lkeypad["text"]  = f"Keypad phase: {keypad}"
    except: pass
    try: gui._lwires["text"]   = f"Wires phase: {wires}"
    except: pass
    try: gui._lbutton["text"]  = f"Button phase: {button}"
    except: pass
    try: gui._ltoggles["text"] = f"Toggles phase: {toggles}"
    except: pass
    try: gui._lstrikes["text"] = f"Strikes left: {strikes_left}"
    except: pass

    # handle failures/defuses
    for phase in (keypad, toggles, wires, button):
        if phase._failed:
            strikes_left  -= 1
            active_phases -= 1
            phase._failed = False
        elif phase._defused:
            active_phases -= 1
            # leave _defused True so the label stays “DEFUSED”

    # continue or finish
    if strikes_left <= 0:
        gui.conclusion(success=False)
    elif active_phases <= 0:
        gui.conclusion(success=True)
    else:
        window.after(100, check_phases)
        
def show_image(path, hold_ms=2000):
    """Full-screen Toplevel that auto-closes after hold_ms."""
    global img_window, img_photo
    if img_window:
        try: img_window.destroy()
        except: pass

    img_window = Toplevel(root)
    img_window.attributes('-fullscreen', True)
    # load & scale
    w, h   = root.winfo_screenwidth(), root.winfo_screenheight()
    img     = Image.open(path).resize((w, h), Image.LANCZOS)
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
    strikes_left   = NUM_STRIKES
    active_phases  = NUM_PHASES
    handled_phases = set()

    # instantiate each phase
    tmr     = Timer(component_7seg, COUNTDOWN)
    kpd     = Keypad(component_keypad, keypad_target)
    wres    = Wires(component_wires,   wires_target)
    btn     = Button(component_button_state,
                     component_button_rgb,
                     button_target, button_color, tmr)
    tgl     = Toggles(component_toggles, toggles_target)

    # connect to GUI
    gui.setTimer(tmr)
    gui.setButton(btn)

    # start threads
    for p in (tmr, kpd, wres, btn, tgl):
        p.start()

    # expose globally for update_gui
    globals().update(timer=tmr,
                     keypad=kpd,
                     wires=wres,
                     button=btn,
                     toggles=tgl)

    # show first challenge
    show_image(challenge_images[0], hold_ms=1500)

# —————————————————————————————————————————————
# GUI update & game logic
# —————————————————————————————————————————————
def update_gui():
    global strikes_left, active_phases

    # 1) refresh LCD labels
    gui.labels['Time']['text']    = f'Time: {timer}'
    gui.labels['Keypad']['text']  = f'Keypad: {keypad}'
    gui.labels['Wires']['text']   = f'Wires: {wires}'
    gui.labels['Button']['text']  = f'Button: {button}'
    gui.labels['Toggles']['text'] = f'Toggles: {toggles}'
    gui.labels['Strikes']['text'] = f'Strikes: {strikes_left}'

    # 2) check each puzzle phase in order
    phase_list = [keypad, wires, toggles, button]
    for idx, phase in enumerate(phase_list):
        if phase in handled_phases:
            continue

        # STRIKE?
        if phase._failed:
            handled_phases.add(phase)
            strikes_left -= 1
            # show strike image
            img_idx = min(NUM_STRIKES - strikes_left - 1, len(strike_images)-1)
            show_image(strike_images[img_idx], hold_ms=1000)
            # reset that phase thread by re-running only that one
            def retry_phase():
                # discard from handled so it can run again
                handled_phases.discard(phase)
                # simple re-setup of that one phase only:
                if idx==0:
                    globals()['keypad'] = Keypad(component_keypad, keypad_target); keypad.start()
                elif idx==1:
                    globals()['wires']  = Wires(component_wires,  wires_target);  wires.start()
                elif idx==2:
                    globals()['toggles']= Toggles(component_toggles,toggles_target);toggles.start()
                else:
                    globals()['button'] = Button(component_button_state,
                                                 component_button_rgb,
                                                 button_target, button_color, timer)
                    button.start()
                root.after(200, update_gui)

            root.after(1200, retry_phase)
            return

        # DEFUSE?
        if phase._defused:
            handled_phases.add(phase)
            active_phases -= 1
            # advance to next challenge image
            next_idx = idx+1
            if next_idx < len(challenge_images):
                show_image(challenge_images[next_idx], hold_ms=1500)
                root.after(1500, update_gui)
            else:
                # all puzzles done → final success
                timer.pause()
                gui.conclusion(True)
            return

    # 3) timer ran out?
    if not timer._running:
        gui.conclusion(False)
        return

    # 4) continue polling
    root.after(100, update_gui)

def start_game():
    gui.setup()
    setup_phases()
    window.after(100, check_phases)
# —————————————————————————————————————————————
# MAIN
# —————————————————————————————————————————————
root = tk.Tk()
gui  = Lcd(root)
gui.setup()

# start everything after GUI is ready
root.after(200, setup_phases)
root.after(500, update_gui)

root.mainloop()
