from tkinter import Tk, Toplevel, Label
from PIL import Image, ImageTk
from bomb_configs import *        # component_7seg, component_keypad, COUNTDOWN, keypad_target, etc.
from bomb_phases import Timer, Keypad, Wires, Button, Toggles, Lcd  # import only needed classes
import random

# File names for images (place these in your working directory)
challenge_images = [
    "KEYPAD.jpeg",  # for keypad
    "meg.jpg",  # for toggles
    "meg.jpg",  # for wires
    "meg.jpg",  # for button
]
strike_images = [
    "STRIKE1.jpeg",
    "STRIKE1.jpeg",
    "STRIKE1.jpeg",
    "STRIKE1.jpeg",
]
game_over_image = "peter_drunk.jpg"
win_image       = "yayyy.jpg"

# Globals for image window
img_window = None
img_photo = None

# Display a fullscreen image in its own window
def show_image(path):
    global img_window, img_photo
    try:
        img_window.destroy()
    except:
        pass
    img_window = Toplevel(window)
    img_window.attributes('-fullscreen', True)
    img_window.lift()
    img_window.focus_force()
    img_window.config(bg='black')
    # load and resize image to screen size
    screen_w = window.winfo_screenwidth()
    screen_h = window.winfo_screenheight()
    img = Image.open(path).resize((screen_w, screen_h), Image.ANTIALIAS)
    img_photo = ImageTk.PhotoImage(img)
    lbl = Label(img_window, image=img_photo)
    lbl.pack(fill='both', expand=True)

# Core GUI & game logic
handled_phases = set()

def check_phases():
    global strikes_left, active_phases, handled_phases
    # update underlying LCD labels (optional)
    try: gui._ltimer["text"]   = f"Time left: {timer}"
    except: pass
    try: gui._lkeypad["text"]  = f"Keypad: {keypad}"
    except: pass
    try: gui._ltoggles["text"] = f"Toggles: {toggles}"
    except: pass
    try: gui._lwires["text"]   = f"Wires: {wires}"
    except: pass
    try: gui._lbutton["text"]  = f"Button: {button}"
    except: pass
    try: gui._lstrikes["text"] = f"Strikes left: {strikes_left}"
    except: pass

    for phase in (keypad, toggles, wires, button):
        if phase in handled_phases:
            continue
        # failure
        if phase._failed:
            strikes_left -= 1
            active_phases -= 1
            handled_phases.add(phase)
            strike_num = len(strike_images) - strikes_left
            if strikes_left > 0 and strike_num <= len(strike_images):
                show_image(strike_images[strike_num-1])
            else:
                show_image(game_over_image)
            gui.conclusion(success=False)
            return
        # defuse
        if phase._defused:
            active_phases -= 1
            handled_phases.add(phase)
            idx = [keypad, toggles, wires, button].index(phase)
            if idx < len(challenge_images)-1:
                show_image(challenge_images[idx+1])
            else:
                show_image(win_image)
                gui.conclusion(success=True)
                return

    # continue polling
    window.after(100, check_phases)

# Initialize phase threads
def setup_phases():
    global timer, keypad, toggles, wires, button, strikes_left, active_phases
    strikes_left  = NUM_STRIKES
    active_phases = NUM_PHASES
    timer   = Timer(component_7seg, COUNTDOWN)
    keypad  = Keypad(component_keypad, "1999")  # hard-coded keypad code
    toggles = Toggles(component_toggles, bin(toggles_target)[2:].zfill(len(component_toggles)))
    wires   = Wires(component_wires, bin(wires_target)[2:].zfill(len(component_wires)))
    button  = Button(component_button_state, component_button_RGB,
                     button_target, button_color, timer)
    gui.setTimer(timer)
    gui.setButton(button)
    for p in (timer, keypad, toggles, wires, button):
        p.start()

# Boot sequence (as before)
def bootup(n=0):
    if not ANIMATE or n >= len(boot_text):
        gui.setup()
    else:
        if boot_text[n] != "\x00":
            gui._lscroll["text"] += boot_text[n]
        delay = 25 if boot_text[n] != "\x00" else 750
        gui.after(delay, bootup, n+1)

# Start game: show first challenge image and begin polling
def start_game():
    gui.setup()
    setup_phases()
    show_image(challenge_images[0])
    window.after(100, check_phases)

# MAIN
window = Tk()
gui = Lcd(window)
gui.after(1000, bootup)
boot_duration = 1000 + len(boot_text)*50
gui.after(boot_duration, start_game)
window.mainloop()
