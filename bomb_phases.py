"""
bomb_phases.py
Defines PhaseThread base class and concrete phase subclasses:
Timer, Keypad, Wires, Toggles, Button, and the Lcd GUI frame.
"""
import time
from threading import Thread
from tkinter import Frame, Label
from PIL import Image, ImageTk
from bomb import *
from bomb_configs import *

##### GUI / LCD #####
class Lcd(Frame):
    def __init__(self, master):
        super().__init__(master, bg="black")
        master.attributes("-fullscreen", True)
        self._timer = None
        self._button = None
        self.pack(fill='both', expand=True)
        if ANIMATE:
            self._boot_label = Label(self, bg="black", fg="white", font=("Courier", 14), justify='left')
            self._boot_label.pack(anchor='nw', padx=20, pady=20)
        else:
            self.setup_game()

    def setup_boot(self):
        try:
            self._boot_label.config(text="")
        except:
            return
        def step(i=0):
            if not hasattr(self, '_boot_label'):
                return
            if i < len(boot_text):
                try:
                    self._boot_label['text'] += boot_text[i]
                    self.after(30, step, i+1)
                except:
                    return
        step()

    def setup_game(self):
        for w in self.winfo_children(): w.destroy()
        font = ("Courier", 16, "bold")
        self._ltime    = Label(self, text="Time: ", fg="#00FF00", bg="black", font=font)
        self._lstrikes = Label(self, text=f"Strikes: {NUM_STRIKES}", fg="#bb105c", bg="black", font=font)
        self._lkeypad  = Label(self, text="Keypad: ...", fg="#FF0000", bg="black", font=font)
        self._lwires   = Label(self, text="Wires: ...", fg="#0000FF", bg="black", font=font)
        self._ltoggles = Label(self, text="Toggles: ...", fg="#d46fb9", bg="black", font=font)
        self._lbutton  = Label(self, text="Button: ...", fg="#23adf5", bg="black", font=font)
        for idx, lbl in enumerate((self._ltime, self._lstrikes,
                                   self._lkeypad, self._lwires,
                                   self._ltoggles, self._lbutton)):
            lbl.place(relx=0.02, rely=0.1 + idx*0.12, anchor='nw')

    def set_timer(self, timer): self._timer = timer
    def set_button(self, button): self._button = button
        
    def update_keypad(self, keypad):
        self._lkeypad['text'] = f"Keypad: {str(keypad)}"
        
    def update_timer(self):
        if self._timer:
            self._ltime['text'] = f"Time: {self._timer.as_mmss()}"
        
    def update_strikes(self, strikes):
        self._lstrikes['text'] = f"Strikes: {strikes}"
        
    def update_toggles(self, toggles):
        self._ltoggles['text']= f"Toggles: {str(toggles)}"
    
    def update_button(self, button):
        self._lbutton['text']  = f"Button: {str(button)}"
    
    def update_wires(self, wires):
        self._lwires['text']   = f"Wires: {str(wires)}"

    def conclude(self, success: bool):
        for w in self.winfo_children(): w.destroy()
        msg = ">>> DEFUSED <<<" if success else "!!! BOOM !!!"
        color = "#00FF00" if success else "#FF0000"
        Label(self, text=msg, fg=color, bg="black", font=("Courier", 32, "bold")).pack(expand=True)

##### Phase base #####
class PhaseThread(Thread):
    def __init__(self, component, target):
        super().__init__(daemon=True)
        self._component = component
        self._target    = str(target)
        self._defused   = False
        self._failed    = False
        self._running   = True
    def defuse(self):
        self._defused = True
        self._running = False
    def fail(self):
        self._failed = True
        self._running = False
    def __str__(self):
        return "DEFUSED" if self._defused else "FAILED" if self._failed else "..."

##### Timer Phase #####
class Timer(PhaseThread):
    def __init__(self, component, initial):
        super().__init__(component, initial)
        self._value = int(initial)
    def run(self):
        while self._running and self._value >= 0:
            mins, secs = divmod(self._value, 60)
            self._component.print(f"{mins:02d}:{secs:02d}")
            time.sleep(1)
            self._value -= 1
        if self._value < 0:
            self.fail()
    def as_mmss(self):
        m, s = divmod(max(self._value,0), 60)
        return f"{m:02d}:{s:02d}"

##### Keypad Phase #####
class Keypad(PhaseThread):
    def __init__(self, component, code):
        super().__init__(component, code)
        self._entry = ""

    def run(self):
        last_key = None
        while self._running and not self._defused:
            keys = getattr(self._component, 'pressed_keys', [])
            if keys:
                key = str(keys[0])
                # only act on a new press
                if key != last_key:
                    last_key = key
                    if key == '*':
                        # reset entry on star
                        self._entry = ""
                    elif key == '#':
                        # submit on hash
                        if self._entry == self._target:
                            self.defuse()
                            return
                        else:
                            self._failed = True
                            # clear entry so user can retry
                            self._entry = ""
                    elif key.isdigit():
                        # append digit
                        self._entry += key
            else:
                # no keys pressed, reset last_key
                last_key = None
            time.sleep(0.05)

    def __str__(self):
        return self._entry or "..."

##### Wires Phase #####
class Wires(PhaseThread):
    def __init__(self, component, pattern):
        super().__init__(component, pattern)
    def run(self):
        while self._running:
            bits = []
            for w in self._component:
                if hasattr(w, 'is_cut'):
                    val = w.is_cut()
                elif hasattr(w, 'read'):
                    val = bool(w.read())
                else:
                    val = bool(getattr(w, 'value', False))
                bits.append('1' if val else '0')
            current = ''.join(bits)
            if current == self._target:
                self.defuse()
            time.sleep(0.1)
    def __str__(self):
        return ''.join('1' if (w.is_cut() if hasattr(w, 'is_cut') else bool(getattr(w, 'value', False))) else '0' for w in self._component)

##### Toggles Phase #####
class Toggles(PhaseThread):
    def __init__(self, component, pattern):
        super().__init__(component, pattern)
    def run(self):
        while self._running:
            current = ''.join(str(int(pin.read() if hasattr(pin, 'read') else pin.value)) for pin in self._component)
            if current == self._target:
                self.defuse()
            time.sleep(0.1)
    def __str__(self):
        return ''.join(str(int(pin.read() if hasattr(pin, 'read') else pin.value)) for pin in self._component)

##### Button Phase #####
class Button(PhaseThread):
    def __init__(self, state_pin, rgb_pins, color, presses, timer_value, timer):
        super().__init__(state_pin, presses)
        self._rgb = rgb_pins
        self._original = color
        self._presses = int(presses)
        self._timer = timer
        self._timer._value = timer_value
        self._count = 0
        self._start_ts = None
        self._submission_mode = (color == 'B')  # Flag for submission mode
        self._current_phase = None              # Track current phase: 'wires', 'toggles', or None
        
        # Light the appropriate LED based on mode
        self.set_color(color)
  
    def set_color(self, color):
        # Turn on only the LED matching `color`
        for i, led in enumerate(self._rgb):
            led.value = (['R','G','B'][i] != color)
        
        # Update submission mode flag when color changes
        self._submission_mode = (color == 'B')

    def set_phase(self, phase_name):
        # Used to tell the button which phase is active
        self._current_phase = phase_name
        
        # Only enable submission mode if we're in Wires or Toggles phase AND button is blue
        if phase_name in ['wires', 'toggles'] and self._original == 'B':
            self.set_color('B')  # Make sure blue is lit
        else:
            self.set_color(self._original)  # Default to original color

    def confirm_current_phase(self):
        # This is called when button is pressed in submission mode
        if self._current_phase == 'wires' and hasattr(self, '_wires_thread'):
            # Check if wires are in correct configuration
            current = self._wires_thread.__str__()
            if current == self._wires_thread._target:
                self._wires_thread.defuse()
            else:
                self._wires_thread.fail()
                
        elif self._current_phase == 'toggles' and hasattr(self, '_toggles_thread'):
            # Check if toggles are in correct configuration
            current = self._toggles_thread.__str__()
            if current == self._toggles_thread._target:
                self._toggles_thread.defuse()
            else:
                self._toggles_thread.fail()

    def set_wires_thread(self, wires_thread):
        # Store reference to wires thread for confirmation
        self._wires_thread = wires_thread
        
    def set_toggles_thread(self, toggles_thread):
        # Store reference to toggles thread for confirmation
        self._toggles_thread = toggles_thread

    def run(self):        
        if self._timer._value == 0:
            self._failed = True
            
        while self._running:
            if self._component.value:  # Button is pressed
                # Wait for release
                while self._component.value:
                    time.sleep(0.02)
                
                # Handle based on mode
                if self._submission_mode and self._current_phase in ['wires', 'toggles']:
                    # Submission mode for Wires or Toggles
                    self.confirm_current_phase()
                else:
                    # Original counting mode
                    # Mark time on first press
                    if self._count == 0:
                        self._start_ts = time.time()
                    self._count += 1
                    
                    # If that was the last press, check speed
                    if self._count >= self._presses:
                        elapsed = time.time() - self._start_ts
                        if elapsed <= self._timer._value:
                            self.defuse()
                        else:
                            self.fail()
                        return
                        
            time.sleep(0.05)

    def __str__(self):
        if self._submission_mode and self._current_phase in ['wires', 'toggles']:
            return f"SUBMIT ({self._current_phase})"
        else:
            return f"{self._count}/{self._presses}"
