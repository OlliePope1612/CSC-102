"""
bomb.py
Entry point for the Defuse the Bomb game with randomized imagery per phase.
"""
import sys
import random
from tkinter import Tk, Toplevel, Label
from PIL import Image, ImageTk
from bomb_configs import *
from bomb_phases import *
import shutil, subprocess
from pygame import mixer

# Global variables
strikes_left = 0  # Will be initialized from NUM_STRIKES
strike_image_audio_index = 1

STRIKE_IMAGES = [
    "STRIKE4.jpeg",
    "STRIKE3.jpeg",
    "STRIKE2.jpeg",
    "STRIKE1.jpeg",
]

# Globals for image popups
global_window = None
img_window    = None
img_photo     = None

# Show a full-screen image and auto-focus it
def show_image(path):
    global img_window, img_photo
    # Destroy previous image window if it exists
    if img_window is not None:
        try:
            img_window.destroy()
        except:
            pass

    # Create new fullscreen image window
    img_window = Toplevel()
    img_window.attributes('-fullscreen', True)

    # Resize and display image
    img = Image.open(path).resize((600, 400), Image.LANCZOS)
    img_photo = ImageTk.PhotoImage(img)
    lbl = Label(img_window, image=img_photo)
    lbl.pack()


# End the game: win or lose
def end_game(gui, success: bool):
    global img_window
    if img_window:
        try: img_window.destroy()
        except: pass
    if success == True:
        mixer.init()
        mixer.music.load('DEFUSED.wav')
        mixer.music.play()
    else:
        mixer.init()
        mixer.music.load('BOOM.wav')
        mixer.music.play()
    gui.conclude(success)

def update_strikes(gui):
    global strikes_left
    gui._lstrikes["text"] = f"Strikes left: {strikes_left}"
        
# Main game loop
def start_game(window, gui):
    global random_button_time
    global strikes_left
    
    # Initialize strikes from imported NUM_STRIKES
    strikes_left = NUM_STRIKES

    gui.setup_game()

    # Start the shared countdown timer
    timer = Timer(component_7seg, COUNTDOWN)
    gui.set_timer(timer)
    timer.start()

    # Helper to randomly pick image+target and instantiate a phase
    phase_images = [None]*4
    phase_audio = [None]*4
    phases = []
    
    def create_phase(i):
        if i == 0:
            # Keypad phase
            r = random.randrange(len(keypad_images))
            r_sound = keypad_audio[r]
            phase_images[0] = keypad_images[r]
            phase_audio[0] = r_sound
            mixer.init()
            mixer.music.load(f'{r_sound}')
            mixer.music.play()
            return Keypad(component_keypad, correct_code[r])
        elif i == 1:
            # Wires phase
            r = random.randrange(len(wires_images))
            r_sound = wires_audio[r]
            phase_images[1] = wires_images[r]
            phase_audio[1] = r_sound
            mixer.init()
            mixer.music.load(f'{r_sound}')
            mixer.music.play()
            return Wires(component_wires, correct_wire[r])
        elif i == 2:
            # Toggles phase
            r = random.randrange(len(toggles_images))
            r_sound = toggles_audio[r]
            phase_images[2] = toggles_images[r]
            phase_audio[2] = r_sound
            mixer.init()
            mixer.music.load(f'{r_sound}')
            mixer.music.play()
            return Toggles(component_toggles, correct_switch_pattern[r])
        else:
            # Button phase: random presses target for each play
            r = random.randrange(len(button_images))
            r_sound = button_audio[r]
            s = random.randint(0,3)
            phase_images[3] = button_images[r]
            phase_audio[3] = r_sound
            mixer.init()
            mixer.music.load(f'{r_sound}')
            mixer.music.play()
            random_button_time = BUTTON_MAX_TIME[s]
            
            # Choose button color based on remaining phases that need to be solved
            # If we still need to solve Wires or Toggles, use Blue button
            # Otherwise use Green button
            if 1 in [p for p in range(len(phases)) if not phases[p]._defused and p < 3 and p > 0]:
                button_mode_color = 'B'  # Blue for submission mode
            else:
                button_mode_color = 'G'  # Green for normal mode
            
            btn = Button(component_button_state,
                        component_button_RGB,
                        button_mode_color,  # Use dynamic color
                        amount_of_presses[s],
                        random_button_time,
                        timer
                        )
            gui.set_button(btn)
            return btn

    # Create and start the first interactive phase
    current = 0
    phase = create_phase(current)
    phases.append(phase)
    phase.start()
    show_image(phase_images[current])
        
    # Controller: polls timer + current phase
    def controller():
        nonlocal current, phase
        global strikes_left
        gui._lstrikes["text"] = f"Strikes left: {strikes_left}"
        
        # Timer expired?
        if timer._failed:
            timer._running = False
            return end_game(gui, False)
        ph = phase
        
        # Failure in this phase?
        if ph._failed:
            strikes_left -= 1
            sound = strike_audio[NUM_STRIKES - strikes_left - 1]
            mixer.init()
            mixer.music.load(f'{sound}')
            mixer.music.play()
            print(f"Strikes left: {strikes_left}")
            show_image(STRIKE_IMAGES[NUM_STRIKES - strikes_left - 1])
            ph._failed = False
            if strikes_left <= 0:
                return end_game(gui, False)
            gui._lstrikes["text"] = f"Strikes left: {strikes_left}"
            # restart same phase after a delay
            window.after(2000, lambda: show_image(phase_images[current]))
            mixer.init()
            mixer.music.load(phase_audio[current])
            mixer.music.play()
            window.after(200, controller)
            return
        # Success in this phase?
        if ph._defused:
            if img_window:
                img_window.destroy()
            current += 1
            if current == 4:
                timer._running = False
                return end_game(gui, True)
            # set up next phase
            phase = create_phase(current)
            phases.append(phase)
            phase.start()
            window.after(500, lambda: show_image(phase_images[current]))
            window.after(200, controller)
            return
        
        # Update phase-specific components
        if current == 0:
            gui.update_keypad(phases[0])
            
            # If Button phase exists and is in Blue mode, reset it to normal mode
            if len(phases) > 3 and hasattr(phases[3], 'set_phase'):
                phases[3].set_phase(None)
                
        elif current == 1:
            gui.update_wires(phases[1])
            
            # If Button phase exists and is in Blue mode, connect it to Wires 
            if len(phases) > 3 and hasattr(phases[3], 'set_phase') and phases[3]._original == 'B':
                phases[3].set_phase('wires')
                phases[3].set_wires_thread(phases[1])
                
        elif current == 2:
            gui.update_toggles(phases[2])
            
            # If Button phase exists and is in Blue mode, connect it to Toggles
            if len(phases) > 3 and hasattr(phases[3], 'set_phase') and phases[3]._original == 'B':
                phases[3].set_phase('toggles')
                phases[3].set_toggles_thread(phases[2])
                
        elif current == 3:
            gui.update_button(phases[3])
            
            # Ensure button is in normal mode with green LED for button phase
            if phases[3]._original == 'G':
                phases[3].set_phase(None)  # Normal mode
                phases[3].set_color('G')
                
        window.after(100, controller)

    # Kick off the controller loop
    window.after(100, controller)

# Entry point
def main():
    global global_window
    global_window = Tk()
    
    gui = Lcd(global_window)

    if ANIMATE:
        gui.after(200, gui.setup_boot)
        gui.after(len(boot_text)*30 + 500, start_game, global_window, gui)
    else:
        start_game(global_window, gui)

    global_window.mainloop()

if __name__ == '__main__':
    main()
