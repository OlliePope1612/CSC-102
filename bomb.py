from tkinter import Tk, Toplevel, Label, Entry, Button, Checkbutton, IntVar
from bomb_configs import *        # brings in component_7seg, component_keypad, etc., plus COUNTDOWN, targets, RPi, correct_code
from bomb_phases import *         # brings in Timer, Keypad, Wires, Button, Toggles, Lcd, and Family Guy lines
import random

# Helper to chain windows once a phase is defused
def after_defuse(phase, callback):
    if phase._defused:
        callback()
    else:
        window.after(100, after_defuse, phase, callback)

# --- KEYPAD PHASE ---
def show_keypad_window():
    top = Toplevel(window)
    top.title("Family Guy Keypad Challenge")
    Label(top, text=random.choice(quagmire_lines), font=("Courier New",16), wraplength=300).pack(pady=10)
    entry = Entry(top, font=("Courier New",18), justify="center")
    entry.pack(pady=10)
    Button(top, text="Submit", font=("Courier New",14), command=lambda: on_keypad_submit(entry, top)).pack(pady=5)
    top.grab_set()

def on_keypad_submit(entry, top):
    if entry.get() == keypad._target:
        keypad.defuse()
        top.destroy()

# --- TOGGLES PHASE ---
def show_switch_window():
    top = Toplevel(window)
    top.title("Family Guy Switch Challenge")
    Label(top, text=random.choice(joe_lines), font=("Courier New",16), wraplength=300).pack(pady=10)
    vars = []
    for i in range(len(toggles._target)):
        v = IntVar(value=0)
        Checkbutton(top, text=f"Switch {i+1}", variable=v, font=("Courier New",14)).pack(anchor="w")
        vars.append(v)
    def submit():
        if "".join(str(v.get()) for v in vars) == toggles._target:
            toggles.defuse(); top.destroy()
    Button(top, text="Submit", font=("Courier New",14), command=submit).pack(pady=5)
    top.grab_set()

# --- WIRES PHASE ---
def show_wires_window():
    top = Toplevel(window)
    top.title("Family Guy Wires Challenge")
    Label(top, text=random.choice(cleveland_lines), font=("Courier New",16), wraplength=300).pack(pady=10)
    for idx, wire in enumerate(component_wires):
        Button(top, text=f"Cut Wire {idx+1}", font=("Courier New",14), command=wire.cut).pack(fill="x", padx=20, pady=2)
    def check_cut():
        if "".join("1" if w.is_cut() else "0" for w in component_wires) == wires._target_bits:
            wires.defuse(); top.destroy()
        else:
            top.after(200, check_cut)
    Button(top, text="Done", font=("Courier New",14), command=check_cut).pack(pady=10)
    top.grab_set()

# --- BUTTON PHASE ---
def show_button_window():
    top = Toplevel(window)
    top.title("Family Guy Button Challenge")
    Label(top, text=random.choice(quagmire_lines + joe_lines + cleveland_lines), font=("Courier New",16), wraplength=300).pack(pady=10)
    def on_press():
        button._component.value = True; button._pressed = True; button._component.value = False
        if button._target is None or str(button._target) in timer._sec:
            button.defuse()
        else:
            button.fail()
        top.destroy()
    Button(top, text="Press Me", font=("Courier New",18), command=on_press).pack(pady=20)
    top.grab_set()

# --- CORE GAME LOGIC ---
def check_phases():
    global strikes_left, active_phases, handled_phases
    for label, phase in (("_ltimer", timer), ("_lkeypad", keypad), ("_lwires", wires), ("_lbutton", button), ("_ltoggles", toggles)):
        try:
            getattr(gui, label)["text"] = f"{label[2:].replace('_',' ').title()}: {phase}"
        except:
            pass
    try:
        gui._lstrikes["text"] = f"Strikes left: {strikes_left}"
    except:
        pass
    for phase in (keypad, wires, button, toggles):
        if phase in handled_phases: continue
        if phase._failed:
            strikes_left -= 1; active_phases -= 1; handled_phases.add(phase)
        elif phase._defused:
            active_phases -= 1; handled_phases.add(phase)
    if strikes_left <= 0:
        gui.conclusion(success=False)
    elif active_phases <= 0:
        gui.conclusion(success=True)
    else:
        window.after(100, check_phases)

# --- PHASE SETUP ---
def setup_phases():
    global timer, keypad, wires, button, toggles, strikes_left, active_phases
    strikes_left = NUM_STRIKES
    active_phases = NUM_PHASES
    timer   = Timer(component_7seg, COUNTDOWN)
    keypad  = Keypad(component_keypad, correct_code)  # use correct_code from bomb_configs
    wires   = Wires(component_wires, bin(wires_target)[2:].zfill(len(component_wires)))
    button  = Button(component_button_state, component_button_RGB, button_target, button_color, timer)
    toggles = Toggles(component_toggles, bin(toggles_target)[2:].zfill(len(component_toggles)))
    gui.setTimer(timer); gui.setButton(button)
    for phase in (timer, keypad, wires, button, toggles): phase.start()

# --- BOOTUP SEQUENCE ---
def bootup(n=0):
    if not ANIMATE or n >= len(boot_text):
        gui.setup()
    else:
        if boot_text[n] != "\x00":
            gui._lscroll["text"] += boot_text[n]
        delay = 25 if boot_text[n] != "\x00" else 750
        gui.after(delay, bootup, n+1)

# --- START GAME ---
def start_game():
    gui.setup()
    setup_phases()
    show_keypad_window()
    after_defuse(keypad, show_switch_window)
    after_defuse(toggles, show_wires_window)
    after_defuse(wires, show_button_window)
    window.after(100, check_phases)

# --- MAIN ---
window = Tk()
gui = Lcd(window)
gui.after(1000, bootup)
boot_duration = 1000 + len(boot_text) * 50
gui.after(boot_duration, start_game)
window.mainloop()
