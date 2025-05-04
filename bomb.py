import tkinter as tk
from bomb_configs import *
from bomb_phases import Timer, Keypad, Wires, Button, Toggles, Lcd

# Global state
strikes_left  = NUM_STRIKES
active_phases = NUM_PHASES

def setup_phases():
    global strikes_left, active_phases
    strikes_left  = NUM_STRIKES
    active_phases = NUM_PHASES

    # instantiate
    tmr     = Timer(component_7seg, COUNTDOWN)
    kpd     = Keypad(component_keypad, keypad_target)
    wres    = Wires(component_wires, wires_target)
    btn     = Button(component_button_state, component_button_rgb, button_target, tmr)
    tgl     = Toggles(component_toggles, toggles_target)

    gui.setTimer(tmr)
    gui.setButton(btn)

    # start all
    for p in (tmr, kpd, wres, btn, tgl):
        p.start()
    # store in globals for UI update
    globals().update(timer=tmr, keypad=kpd, wires=wres, button=btn, toggles=tgl)

def update_gui():
    global strikes_left, active_phases

    # 1) Refresh labels
    gui.labels['Time']['text']    = f'Time: {timer}'
    gui.labels['Keypad']['text']  = f'Keypad: {keypad}'
    gui.labels['Wires']['text']   = f'Wires: {wires}'
    gui.labels['Button']['text']  = f'Button: {button}'
    gui.labels['Toggles']['text'] = f'Toggles: {toggles}'
    gui.labels['Strikes']['text'] = f'Strikes: {strikes_left}'

    # 2) Check for strikes or defuses
    for phase in (keypad, wires, button, toggles):
        if phase._failed:
            strikes_left  -= 1
            active_phases -= 1
            phase._failed = False
        elif phase._defused:
            active_phases -= 1

    # 3) End or continue
    if strikes_left <= 0:
        gui.conclusion(False)
    elif active_phases <= 0:
        timer.pause()          # stop timer
        gui.conclusion(True)
    else:
        gui.after(200, update_gui)

# --- main ---
root = tk.Tk()
gui  = Lcd(root)
gui.setup()
setup_phases()
gui.after(200, update_gui)
root.mainloop()
