rom tkinter import Tk, Toplevel, Label
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

# Track phases
handled_phases = set()
# We'll create phase variables but only start threads in sequence
timer = keypad = toggles = wires = button = None
strikes_left = 0
active_phases = 0

# Boot sequence
def bootup(n=0):
    if not ANIMATE or n >= len(boot_text):
        gui.setup()
    else:
        if boot_text[n] != "\x00": gui._lscroll["text"] += boot_text[n]
        delay = 25 if boot_text[n] != "\x00" else 750
        gui.after(delay, bootup, n+1)

# Initialize only timer and keypad
def setup_phases():
    global timer, keypad, strikes_left, active_phases
    strikes_left  = NUM_STRIKES
    active_phases = 5
    timer = Timer(component_7seg, COUNTDOWN)
    keypad = Keypad(component_keypad, "1999")
    gui.setTimer(timer)
    gui.setButton(None)
    timer.start()
    keypad.start()
    # show first challenge
    show_image(challenge_images[0])

# Sequentially start next phase
def start_toggles():
    global toggles
    toggles = Toggles(component_toggles, "1010")
    toggles.start()
    show_image(challenge_images[1])

def start_wires():
    global wires
    wires = Wires(component_wires, bin(wires_target)[2:].zfill(len(component_wires)))
    wires.start()
    show_image(challenge_images[2])

def start_button():
    global button
    button = Button(component_button_state, component_button_RGB, button_target, button_color, timer)
    button.start()
    show_image(challenge_images[3])

# Poll and chain phases
def check_phases():
    global strikes_left, active_phases
    # Keypad
    if keypad._defused and 'keypad' not in handled_phases:
        handled_phases.add('keypad')
        start_toggles()
    # Toggles
    if 'keypad' in handled_phases and toggles and toggles._defused and 'toggles' not in handled_phases:
        handled_phases.add('toggles')
        start_wires()
    # Wires
    if 'toggles' in handled_phases and wires and wires._defused and 'wires' not in handled_phases:
        handled_phases.add('wires')
        start_button()
    # Button
    if 'wires' in handled_phases and button and button._defused and 'button' not in handled_phases:
        handled_phases.add('button')
        show_image(win_image)
        gui.conclusion(success=True)
        return
    # Failures: if any phase fails
    for phase_name, phase_obj, img_idx in [
        ('keypad', keypad, 0),
        ('toggles', toggles,1),
        ('wires', wires,2),
        ('button',button,3)
    ]:
        if phase_obj and phase_obj._failed and phase_name not in handled_phases:
            handled_phases.add(phase_name)
            strikes_left -= 1
            show_image(strike_images[img_idx])
            def restore():
                # reset fail state
                phase_obj._failed = False
                handled_phases.discard(phase_name)
                # retry same phase
                if phase_name=='keypad': keypad.start(); show_image(challenge_images[0])
                if phase_name=='toggles': toggles.start(); show_image(challenge_images[1])
                if phase_name=='wires': wires.start(); show_image(challenge_images[2])
                if phase_name=='button': button.start(); show_image(challenge_images[3])
                window.after(100, check_phases)
            if strikes_left>0:
                window.after(5000, restore)
            else:
                window.after(5000, lambda: show_image(game_over_image))
                window.after(5000, lambda: gui.conclusion(success=False))
            return
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

