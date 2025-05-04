#################################
# CSC 102 Defuse the Bomb Project
# Main program – Day 3 GUI integration
#################################

from tkinter import Tk, Toplevel, Label, Entry, Button, Checkbutton, IntVar
from bomb_configs import *        # brings in component_7seg, component_keypad, etc., plus COUNTDOWN, targets, RPi
from bomb_phases import *         # brings in Timer, Keypad, Wires, Button, Toggles, Lcd, and Family Guy lines
import random

# Dialogue maps imported via bomb_phases: quagmire_lines, joe_lines, cleveland_lines

handled_phases = set()

###########
# Helper functions for Family Guy windows
###########

def after_defuse(phase, callback):
    """Invoke callback once phase._defused becomes True."""
    if phase._defused:
        callback()
    else:
        window.after(100, after_defuse, phase, callback)

# --- KEYPAD PHASE WINDOW ---
def show_keypad_window():
    top = Toplevel(window)
    top.title("Family Guy Keypad Challenge")
    Label(top, text=random.choice(quagmire_lines),
          font=("Courier New",16), wraplength=300).pack(pady=10)
    entry = Entry(top, font=("Courier New",18), justify="center")
    entry.pack(pady=10)
    Button(top, text="Submit", font=("Courier New",14),
           command=lambda: on_keypad_submit(entry, top)).pack(pady=5)
    top.grab_set()

def on_keypad_submit(entry, top):
    if entry.get() == keypad._target:
        keypad.defuse()
        top.destroy()

# --- SWITCHES (TOGGLES) PHASE WINDOW ---
def show_switch_window():
    top = Toplevel(window)
    top.title("Family Guy Switch Challenge")
    Label(top, text=random.choice(joe_lines),
          font=("Courier New",16), wraplength=300).pack(pady=10)

    vars = []
    # create checkbuttons to build the toggle bitstring
    for i in range(len(toggles._target)):
        v = IntVar(value=0)
        cb = Checkbutton(top, text=f"Switch {i+1}", variable=v,
                         font=("Courier New",14))
        cb.pack(anchor="w")
        vars.append(v)

    def submit():
        pattern = "".join(str(v.get()) for v in vars)
        if pattern == toggles._target:
            toggles.defuse()
            top.destroy()

    Button(top, text="Submit", font=("Courier New",14),
           command=submit).pack(pady=5)
    top.grab_set()

# --- WIRES PHASE WINDOW ---
def show_wires_window():
    top = Toplevel(window)
    top.title("Family Guy Wires Challenge")
    Label(top, text=random.choice(cleveland_lines),
          font=("Courier New",16), wraplength=300).pack(pady=10)
    # simple UI: buttons to cut wires
    for idx, wire in enumerate(component_wires):
        btn = Button(top, text=f"Cut Wire {idx+1}", font=("Courier New",14),
                     command=wire.cut)
        btn.pack(fill="x", padx=20, pady=2)

    def check_cut():
        bits = "".join("1" if w.is_cut() else "0" for w in component_wires)
        if bits == wires._target_bits:
            wires.defuse()
            top.destroy()
        else:
            top.after(200, check_cut)

    Button(top, text="Done", font=("Courier New",14),
           command=check_cut).pack(pady=10)
    top.grab_set()

# --- BUTTON PHASE WINDOW ---
def show_button_window():
    top = Toplevel(window)
    top.title("Family Guy Button Challenge")
    Label(top, text=random.choice(quagmire_lines + joe_lines + cleveland_lines),
          font=("Courier New",16), wraplength=300).pack(pady=10)

    def on_press():
        # simulate press/release events
        button._component.value = True
        button._pressed = True
        button._component.value = False
        # evaluate target logic
        if (button._target is None or str(button._target) in timer._sec):
            button.defuse()
        else:
            button.fail()
        top.destroy()

    Button(top, text="Press Me", font=("Courier New",18),
           command=on_press).pack(pady=20)
    top.grab_set()

###########
# Existing game logic
###########
def check_phases():
    global strikes_left, active_phases, handled_phases
    try: gui._ltimer  ["text"] = f"Time left: {timer}"
    except: pass
    try: gui._lkeypad["text"] = f"Keypad phase: {keypad}"
    except: pass
    try: gui._lwires  ["text"] = f"Wires phase: {wires}"
    except: pass
    try: gui._lbutton ["text"] = f"Button phase: {button}"
    except: pass
    try: gui._ltoggles["text"] = f"Toggles phase: {toggles}"
    except: pass
    try: gui._lstrikes["text"] = f"Strikes left: {strikes_left}"
    except: pass

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
    wires   = Wires(component_wires, bin(wires_target)[2:].zfill(len(component_wires)))
    button  = Button(component_button_state, component_button_RGB,
                     button_target, button_color, timer)
    toggles = Toggles(component_toggles, bin(toggles_target)[2:].zfill(len(component_toggles)))

    gui.setTimer(timer)
    gui.setButton(button)

    for phase in (timer, keypad, wires, button, toggles):
        phase.start()

# boot sequence
window = Tk()
 gui = Lcd(window)
 gui.after(1000, bootup)
# schedule game start after boot scroll
boot_duration = 1000 + len(boot_text) * 50
 gui.after(boot_duration, start_game)

window.mainloop()

# Updated start_game to chain puzzles
 def start_game():
    gui.setup()
    setup_phases()

    # launch puzzles in order
    show_keypad_window()
    after_defuse(keypad, show_switch_window)
    after_defuse(toggles, show_wires_window)
    after_defuse(wires,   show_button_window)

    window.after(100, check_phases)


