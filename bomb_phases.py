#################################
# CSC 102 Defuse the Bomb Project
# GUI and Phase class definitions
# Team: Lucas and Kobe
#################################

# import the configs
from bomb_configs import *
# other imports
from tkinter import *
import tkinter
from threading import Thread
from time import sleep
import os
import sys

#########
# classes
#########
# the LCD display GUI
# the LCD display GUI
class Lcd(Frame):
    def __init__(self, window):
        super().__init__(window, bg="black")
        # make the GUI fullscreen
        window.attributes("-fullscreen", True)

        # we need to know about the timer (7-segment display) to be able to pause/unpause it
        self._timer = None
        # we need to know about the pushbutton to turn off its LED when the program exits
        self._button = None

        # pack the main frame
        self.pack(fill=BOTH, expand=True)

        # setup the initial "boot" GUI
        self.setupBoot()

    # sets up the LCD "boot" GUI
    def setupBoot(self):
        # create a frame for boot text (top)
        self.boot_frame = Frame(self, bg="black")
        self.boot_frame.grid(row=0, column=0, sticky="nw")

        # create a frame for the bomb status UI (bottom)
        self.bomb_frame = Frame(self, bg="black")
        self.bomb_frame.grid(row=1, column=0, sticky="nw")

        # optional initial boot label (used by some code, safe to keep)
        self._lscroll = Label(
            self.boot_frame,
            bg="black",
            fg="white",
            font=("Courier New", 14),
            text="",
            justify=LEFT
        )
        self._lscroll.pack(anchor="w")

        # list to hold extra boot labels if you animate/add lines
        self.boot_labels = []
        self._boot_index = 0

    # sets up the LCD GUI (bomb info) in the bomb_frame so it doesn't overlap boot text
    def setup(self):
        # the timer
        self._ltimer = Label(self.bomb_frame, bg="black", fg="#00ff00",
                             font=("Courier New", 18), text="Time left: ")
        self._ltimer.grid(row=0, column=0, columnspan=3, sticky=W)
        # the keypad passphrase
        self._lkeypad = Label(self.bomb_frame, bg="black", fg="#00ff00",
                              font=("Courier New", 18), text="Keypad phase: ")
        self._lkeypad.grid(row=1, column=0, columnspan=3, sticky=W)
        # the jumper wires status
        self._lwires = Label(self.bomb_frame, bg="black", fg="#00ff00",
                             font=("Courier New", 18), text="Wires phase: ")
        self._lwires.grid(row=2, column=0, columnspan=3, sticky=W)
        # the pushbutton status
        self._lbutton = Label(self.bomb_frame, bg="black", fg="#00ff00",
                              font=("Courier New", 18), text="Button phase: ")
        self._lbutton.grid(row=3, column=0, columnspan=3, sticky=W)
        # the toggle switches status
        self._ltoggles = Label(self.bomb_frame, bg="black", fg="#00ff00",
                               font=("Courier New", 18), text="Toggles phase: ")
        self._ltoggles.grid(row=4, column=0, columnspan=2, sticky=W)
        # the strikes left
        self._lstrikes = Label(self.bomb_frame, bg="black", fg="#00ff00",
                               font=("Courier New", 18), text="Strikes left: ")
        self._lstrikes.grid(row=4, column=2, sticky=W)

        if (SHOW_BUTTONS):
            # the pause button (pauses the timer)
            self._bpause = tkinter.Button(self.bomb_frame, bg="red", fg="white",
                                          font=("Courier New", 18), text="Pause",
                                          anchor=CENTER, command=self.pause)
            self._bpause.grid(row=5, column=0, pady=40)
            # the quit button
            self._bquit = tkinter.Button(self.bomb_frame, bg="red", fg="white",
                                         font=("Courier New", 18), text="Quit",
                                         anchor=CENTER, command=self.quit)
            self._bquit.grid(row=5, column=2, pady=40)

    # lets us pause/unpause the timer (7-segment display)
    def setTimer(self, timer):
        self._timer = timer

    # lets us turn off the pushbutton's RGB LED
    def setButton(self, button):
        self._button = button

    # pauses the timer
    def pause(self):
        if (RPi):
            self._timer.pause()

    # setup the conclusion GUI (explosion/defusion)
    def conclusion(self, success=False):
        # clear boot text (if you want to blank it)
        if hasattr(self, "_lscroll"):
            self._lscroll["text"] = ""

        # destroy bomb UI widgets
        self._ltimer.destroy()
        self._lkeypad.destroy()
        self._lwires.destroy()
        self._lbutton.destroy()
        self._ltoggles.destroy()
        self._lstrikes.destroy()
        if (SHOW_BUTTONS):
            self._bpause.destroy()
            self._bquit.destroy()

        # reconfigure the GUI
        self._bretry = tkinter.Button(self.bomb_frame, bg="red", fg="white",
                                      font=("Courier New", 18), text="Retry",
                                      anchor=CENTER, command=self.retry)
        self._bretry.grid(row=1, column=0, pady=40)

        self._bquit = tkinter.Button(self.bomb_frame, bg="red", fg="white",
                                     font=("Courier New", 18), text="Quit",
                                     anchor=CENTER, command=self.quit)
        self._bquit.grid(row=1, column=2, pady=40)

    # re-attempts the bomb (after an explosion or a successful defusion)
    def retry(self):
        os.execv(sys.executable, ["python3"] + [sys.argv[0]])
        exit(0)

    # quits the GUI, resetting some components
    def quit(self):
        if (RPi):
            # turn off the 7-segment display
            self._timer._running = False
            self._timer._component.blink_rate = 0
            self._timer._component.fill(0)
            # turn off the pushbutton's LED
            for pin in self._button._rgb:
                pin.value = True
        exit(0)


# template (superclass) for various bomb components/phases
class PhaseThread(Thread):
    def __init__(self, name, component=None, target=None):
        super().__init__(name=name, daemon=True)
        # phases have an electronic component (which usually represents the GPIO pins)
        self._component = component
        # phases have a target value (e.g., a specific combination on the keypad, the proper jumper wires to "cut", etc)
        self._target = target
        # phases can be successfully defused
        self._defused = False
        # phases can be failed (which result in a strike)
        self._failed = False
        # phases have a value (e.g., a pushbutton can be True/Pressed or False/Released, several jumper wires can be "cut"/False, etc)
        self._value = None
        # phase threads are either running or not
        self._running = False

# the timer phase
class Timer(PhaseThread):
    def __init__(self, component, initial_value, name="Timer"):
        super().__init__(name, component)
        # the default value is the specified initial value
        self._value = initial_value
        # is the timer paused?
        self._paused = False
        # initialize the timer's minutes/seconds representation
        self._min = ""
        self._sec = ""
        # by default, each tick is 1 second
        self._interval = 1

    # runs the thread
    def run(self):
        self._running = True
        while (self._running):
            if (not self._paused):
                # update the timer and display its value on the 7-segment display
                self._update()
                self._component.print(str(self))
                # wait 1s (default) and continue
                sleep(self._interval)
                # the timer has expired -> phase failed (explode)
                if (self._value == 0):
                    self._running = False
                self._value -= 1
            else:
                sleep(0.1)

    # updates the timer (only internally called)
    def _update(self):
        self._min = f"{self._value // 60}".zfill(2)
        self._sec = f"{self._value % 60}".zfill(2)

    # pauses and unpauses the timer
    def pause(self):
        # toggle the paused state
        self._paused = not self._paused
        # blink the 7-segment display when paused
        self._component.blink_rate = (2 if self._paused else 0)

    # returns the timer as a string (mm:ss)
    def __str__(self):
        return f"{self._min}:{self._sec}"

# the keypad phase
class Keypad(PhaseThread):
    def __init__(self, component, target, name="Keypad"):
        super().__init__(name, component, target)
        # the default value is an empty string
        self._value = ""

    # runs the thread
    def run(self):
        self._running = True
        while (self._running):
            # process keys when keypad key(s) are pressed
            if (self._component.pressed_keys):
                # debounce
                while (self._component.pressed_keys):
                    try:
                        # just grab the first key pressed if more than one were pressed
                        key = self._component.pressed_keys[0]
                    except:
                        key = ""
                    sleep(0.1)
                # log the key
                self._value += str(key)
                # the combination is correct -> phase defused
                if (self._value == self._target):
                    self._defused = True
                # the combination is incorrect -> phase failed (strike)
                elif (self._value != self._target[0:len(self._value)]):
                    self._failed = True
            sleep(0.1)

    # returns the keypad combination as a string
    def __str__(self):
        if (self._defused):
            return "DEFUSED"
        else:
            return self._value

# the jumper wires phase
class Wires(PhaseThread):
    def __init__(self, component, target, name="Wires"):
        super().__init__(name, component, target)

    def run(self):
        self._running = True
        while self._running:
            # read wire states (True = cut, False = connected)
            wire_states = [pin.value for pin in self._component]

            # convert to binary string
            bits = "".join("1" if state else "0" for state in wire_states)

            # if your wires are read MSB → LSB but your target assumes LSB → MSB, reverse:
            current_value = int(bits[::-1], 2)

            # DEBUG: see what is being read
            print(f"Wire states: {wire_states} | Bits: {bits} | Reversed Decimal: {current_value} | Target: {self._target}")

            # check if it matches the target
            if current_value == self._target:
                self._defused = True
                print("Wires DEFUSED!")  # DEBUG
                # do NOT stop _running here; the main loop will handle stopping
            else:
                self._defused = False

            sleep(0.1)

    def __str__(self):
        if self._defused:
            return "DEFUSED"
        else:
            # show current wire pattern in binary
            bits = "".join("1" if pin.value else "0" for pin in self._component)
            return bits





# the pushbutton phase# the pushbutton phase
class Button(PhaseThread):
    def __init__(self, component_state, component_rgb, target, color, timer, name="Button"):
        super().__init__(name, component_state, target)
        self._value = False
        self._pressed = False
        self._rgb = component_rgb
        self._color = color
        self._timer = timer

        self._press_count = 0   # NEW: count presses

    def run(self):
        self._running = True

        # Set the RGB LED color
        self._rgb[0].value = False if self._color == "R" else True
        self._rgb[1].value = False if self._color == "G" else True
        self._rgb[2].value = False if self._color == "B" else True

        while self._running:
            self._value = self._component.value

            # If button is pressed
            if self._value:
                self._pressed = True

            # If button is released → count a full press
            else:
                if self._pressed:
                    self._press_count += 1
                    print("Button presses:", self._press_count)

                    # Defuse after 5 presses
                    if self._press_count >= 5:
                        self._defused = True

                    self._pressed = False

            sleep(0.1)

    def __str__(self):
        if self._defused:
            return "DEFUSED"
        else:
            return f"Pressed {self._press_count} times"


# the toggle switches phase
class Toggles(PhaseThread):
    def __init__(self, component, target, name="Toggles"):
        super().__init__(name, component, target)

    def run(self):
        self._running = True
        while self._running:

            # Read toggle states
            toggle_states = [pin.value for pin in self._component]

            # Convert to binary string
            bits = "".join("1" if state else "0" for state in toggle_states)

            # Convert binary to integer
            current_value = int(bits, 2)

            # Check if correct
            if current_value == self._target:
                self._defused = True      # mark defused
                # DO NOT STOP THREAD HERE
            else:
                self._defused = False

            sleep(0.1)

    def __str__(self):
        if self._defused:
            return "DEFUSED"
        else:
            bits = "".join("1" if pin.value else "0" for pin in self._component)
            return bits
