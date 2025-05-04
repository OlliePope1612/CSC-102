from tkinter import Tk, Toplevel, Label
from PIL import Image, ImageTk
from bomb_configs import *        # hardware components & constants
from bomb_phases import Timer, Keypad, Wires, Button, Toggles, Lcd

# File names for images
challenge_images = [
    "KEYPAD.jpeg",  # keypad challenge
    "TOGGLES.jpeg",     # toggles challenge
    "WIRES.jpeg",     # wires challenge
    "BUTTON.jpeg",     # button challenge
]
strike_images = [
    "STRIKE1.jpeg",
    "STRIKE2.jpeg",
    "STRIKE3.jpeg",
    "STRIKE4.jpeg",
]
game_over_image = "FAILURE.jpeg"
win_image       = "DEFUSED.jpeg"

# Globals for image window
img_window = None
img_photo  = None

# Core state
strikes_left    = 0
active_phases   = 0
handled_phases  = set()

# Helper: display fullscreen image
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
    screen_w = window.winfo_screenwidth()
    screen_h = window.winfo_screenheight()
    img = Image.open(path).resize((screen_w, screen_h), Image.LANCZOS)
    img_photo = ImageTk.PhotoImage(img)
    lbl = Label(img_window, image=img_photo)
    lbl.pack(fill='both', expand=True)

def check_phases():
    global timer, keypad, wires, button, toggles, strikes_left, active_phases

    # While there are still phases to defuse and you haven’t exploded…
    while active_phases > 0 and strikes_left > 0:
        # 1) Refresh every label (wrapped in try/except so we don’t crash
        #    if that widget has already been destroyed by conclusion())
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

        # 2) Look at each non-timer phase:
        for phase in (keypad, wires, button, toggles):
            if phase._failed:
                # somebody got it wrong → lose a strike
                strikes_left  -= 1
                active_phases -= 1
                phase._failed  = False
            elif phase._defused:
                # that phase is done for good
                active_phases -= 1
                # (we leave phase._defused True so the label stays “DEFUSED”)

        # 3) Give control back to Tk so the GUI remains responsive
        gui.update()
        gui.after(100)   # schedule next check in 100 ms
        return           # IMPORTANT! return here so the loop is driven by after()

    # 4) Once you exit the loop, show your final banner
    gui.conclusion(success=(active_phases == 0))

# Initialize and start all phases
def setup_phases():
    global timer, keypad, toggles, wires, button, strikes_left, active_phases, handled_phases
    strikes_left    = NUM_STRIKES
    active_phases   = NUM_PHASES
    handled_phases  = set()

    timer   = Timer(component_7seg, COUNTDOWN)
    keypad  = Keypad(component_keypad, str(keypad_target))
    toggles = Toggles(component_toggles, bin(toggles_target)[2:].zfill(len(component_toggles)))
    wires   = Wires(component_wires, bin(wires_target)[2:].zfill(len(component_wires)))
    button  = Button(
        component_button_state,
        component_button_RGB,
        button_target, button_color, timer,
        submit_phases=(toggles, wires)
    )

    gui.setTimer(timer)
    gui.setButton(button)

    for phase in (timer, keypad, toggles, wires, button):
        phase.start()

    # show first challenge image
    show_image(challenge_images[0])

# Boot sequence
def bootup(n=0):
    if not ANIMATE or n >= len(boot_text):
        gui.setup()
    else:
        if boot_text[n] != "\x00":
            gui._lscroll["text"] += boot_text[n]
        delay = 25 if boot_text[n] != "\x00" else 750
        gui.after(delay, bootup, n+1)

# Start game
def start_game():
    gui.setup()
    setup_phases()
    window.after(100, check_phases)

# MAIN
window = Tk()
gui    = Lcd(window)
gui.after(1000, bootup)
boot_duration = 1000 + len(boot_text) * 50
gui.after(boot_duration, start_game)
window.mainloop()
