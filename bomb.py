from tkinter import Tk, Toplevel, Label
from PIL import Image, ImageTk
from bomb_configs import *        # component_7seg, component_keypad, COUNTDOWN, etc.
from bomb_phases import Timer, Keypad, Wires, Button, Toggles, Lcd
import random

# File names for images
challenge_images = [
    "KEYPAD.jpeg",
    "meg.jpg",
    "meg.jpg",
    "meg.jpg",
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
global img_window, img_photo
img_window = None
img_photo  = None

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
    screen_w = window.winfo_screenwidth()
    screen_h = window.winfo_screenheight()
    img = Image.open(path).resize((screen_w, screen_h), Image.LANCZOS)
    img_photo = ImageTk.PhotoImage(img)
    lbl = Label(img_window, image=img_photo)
    lbl.pack(fill='both', expand=True)

# Core GUI & game logic
handled_phases = set()

# Track phase threads
timer = None
keypad = None
toggles = None
wires = None
button = None

# Boot sequence
def bootup(n=0):
    if not ANIMATE or n >= len(boot_text):
        gui.setup()
    else:
        if boot_text[n] != "\x00":
            gui._lscroll["text"] += boot_text[n]
        delay = 25 if boot_text[n] != "\x00" else 750
        gui.after(delay, bootup, n+1)

# Initialize and start all phases at once
def setup_phases():
    global timer, keypad, toggles, wires, button, strikes_left, active_phases
    strikes_left  = NUM_STRIKES
    active_phases = NUM_PHASES

    timer   = Timer(component_7seg, COUNTDOWN)
    keypad  = Keypad(component_keypad, "1999")       # hard-coded code
    toggles = Toggles(component_toggles, "1010")     # hard-coded toggles target
    wires   = Wires(component_wires, "10101")  # hard-coded odd-numbered wires 1,3,5[2:].zfill(len(component_wires)))
    button  = Button(component_button_state, component_button_RGB,
                     button_target, button_color, timer)

    gui.setTimer(timer)
    gui.setButton(button)

    # start all threads
    for phase in (timer, keypad, toggles, wires, button):
        phase.start()

    # show first challenge image
    show_image(challenge_images[0])

# Poll phases for defuse/fail and advance
def check_phases():
    global strikes_left, active_phases
    # Update underlying labels (optional)
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

    # Check each phase in order
    for idx, phase in enumerate((keypad, toggles, wires, button)):
        if phase in handled_phases:
            continue
        # failure handling
        if phase._failed:
            handled_phases.add(phase)
            strikes_left -= 1
            # show strike image
            show_image(strike_images[min(idx, len(strike_images)-1)])
            # after 5s, either game over or re-show challenge
            def next_step():
                if strikes_left > 0:
                    show_image(challenge_images[idx])
                else:
                    show_image(game_over_image)
                    gui.conclusion(success=False)
            window.after(5000, next_step)
            return
        # defuse handling
        if phase._defused:
            handled_phases.add(phase)
            active_phases -= 1
            # advance: show next challenge or win
            if idx < len(challenge_images)-1:
                show_image(challenge_images[idx+1])
            else:
                show_image(win_image)
                gui.conclusion(success=True)
            return

    # continue polling
    window.after(100, check_phases)

# Start game after boot
def start_game():
    gui.setup()
    setup_phases()
    window.after(100, check_phases)

# MAIN
window = Tk()
gui = Lcd(window)
gui.after(1000, bootup)
boot_duration = 1000 + len(boot_text)*50
gui.after(boot_duration, start_game)
window.mainloop()
