#################################
# CSC 102 Defuse the Bomb Project
# Main program w/ Family Guy “icing”
#################################

import tkinter as tk
from tkinter import Toplevel, Label
from PIL import Image, ImageTk
from bomb_configs import *                # hardware components & constants
from bomb_phases  import Timer, Keypad, Wires, Button as PhaseButton, Toggles, Lcd

# —————————————————————————————————————————————
# Full-screen image helper
# —————————————————————————————————————————————
img_window = None
img_photo  = None

def show_image(path, hold_ms=None):
    """Pop up a full-screen image.  If hold_ms is None, it stays until replaced."""
    global img_window, img_photo
    if img_window:
        try: img_window.destroy()
        except: pass

    img_window = Toplevel(root)
    img_window.attributes('-fullscreen', True)
    w, h = root.winfo_screenwidth(), root.winfo_screenheight()
    img = Image.open(path).resize((w, h), Image.LANCZOS)
    img_photo = ImageTk.PhotoImage(img)
    Label(img_window, image=img_photo).pack(fill='both', expand=True)

    if hold_ms is not None:
        root.after(hold_ms, img_window.destroy)

# —————————————————————————————————————————————
# Challenge & strike images
# —————————————————————————————————————————————
challenge_images = [
    "KEYPAD.jpeg",   # phase 0
    "WIRES.jpeg",    # phase 1
    "TOGGLES.jpeg",  # phase 2
    "BUTTON.jpeg",   # phase 3
]
strike_images = [
    "STRIKE1.jpeg",
    "STRIKE2.jpeg",
    "STRIKE3.jpeg",
]

# —————————————————————————————————————————————
# Global state & phase placeholders
# —————————————————————————————————————————————
strikes_left   = NUM_STRIKES
active_phases  = NUM_PHASES
handled_phases = set()
timer = keypad = wires = toggles = button = None

# —————————————————————————————————————————————
# Build and start the five phase-threads
# —————————————————————————————————————————————
def setup_phases():
    global strikes_left, active_phases, handled_phases
    global timer, keypad, wires, toggles, button

    strikes_left   = NUM_STRIKES
    active_phases  = NUM_PHASES
    handled_phases = set()

    timer   = Timer(component_7seg, COUNTDOWN)
    keypad  = Keypad(component_keypad,      str(keypad_target))
    wires   = Wires(component_wires,        bin(wires_target)[2:].zfill(len(component_wires)))
    toggles = Toggles(component_toggles,    bin(toggles_target)[2:].zfill(len(component_toggles)))
    button  = PhaseButton(
                  component_button_state,
                  component_button_rgb,
                  button_target, button_color,
                  timer,
                  submit_phases=(wires, toggles)
              )

    gui.setTimer(timer)
    gui.setButton(button)

    for p in (timer, keypad, wires, toggles, button):
        p.start()

    # show the intro image & then kick off the polling loop
    show_image(challenge_images[0], hold_ms=None)

    # give the user time to see it, then poll
    root.after(100, update_gui)

# —————————————————————————————————————————————
# Polling loop: refresh LCD, handle strikes/defuses
# —————————————————————————————————————————————
def update_gui():
    global strikes_left, active_phases

    # if any phase still hasn’t been created, wait a bit
    if None in (timer, keypad, wires, toggles, button):
        root.after(100, update_gui)
        return

    # 1) Refresh the LCD labels
    try: gui._ltimer[  "text"] = f"Time left: {timer}"
    except: pass
    try: gui._lkeypad["text"] = f"Keypad phase: {keypad}"
    except: pass
    try: gui._lwires[  "text"] = f"Wires phase: {wires}"
    except: pass
    try: gui._ltoggles["text"] = f"Toggles phase: {toggles}"
    except: pass
    try: gui._lbutton["text"] = f"Button phase: {button}"
    except: pass
    try: gui._lstrikes["text"] = f"Strikes left: {strikes_left}"
    except: pass

    # 2) Check each challenge phase in order
    for idx, phase in enumerate((keypad, wires, toggles, button)):
        # skip phases we've already handled
        if phase in handled_phases:
            continue

        # a) wrong → strike
        if getattr(phase, "_failed", False):
            handled_phases.add(phase)
            strikes_left -= 1
            img_idx = min(NUM_STRIKES - strikes_left - 1, len(strike_images)-1)
            show_image(strike_images[img_idx], hold_ms=2000)
            # reset just that phase after the strike splash
            def retry():
                handled_phases.discard(phase)
                if idx == 0:
                    globals()['keypad'] = Keypad(component_keypad, str(keypad_target))
                    keypad.start()
                elif idx == 1:
                    globals()['wires'] = Wires(component_wires, bin(wires_target)[2:].zfill(len(component_wires)))
                    wires.start()
                elif idx == 2:
                    globals()['toggles'] = Toggles(component_toggles, bin(toggles_target)[2:].zfill(len(component_toggles)))
                    toggles.start()
                else:
                    globals()['button'] = PhaseButton(
                        component_button_state,
                        component_button_rgb,
                        button_target, button_color,
                        timer,
                        submit_phases=(wires, toggles)
                    )
                    button.start()
                root.after(100, update_gui)

            root.after(2000, retry)
            return

        # b) correct → defuse
        if getattr(phase, "_defused", False):
            handled_phases.add(phase)
            active_phases -= 1
            next_idx = idx + 1
            if next_idx < len(challenge_images):
                show_image(challenge_images[next_idx], hold_ms=None)
                root.after(100, update_gui)
            else:
                # all done → success
                timer.pause()
                gui.conclusion(success=True)
            return

    # 3) timer ran out?
    if not getattr(timer, "_running", False):
        gui.conclusion(success=False)
        return

    # 4) keep polling
    root.after(100, update_gui)

# —————————————————————————————————————————————
# Main
# —————————————————————————————————————————————
root = tk.Tk()
gui  = Lcd(root)
gui.setup()

# once the GUI is visible, build & start everything
root.after(200, setup_phases)

root.mainloop()
