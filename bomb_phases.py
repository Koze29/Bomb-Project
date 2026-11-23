"""Tkinter interface and worker-thread implementations for bomb phases."""
import os
import sys
from threading import Thread
from time import sleep
import tkinter
from tkinter import BOTH, LEFT, W, Frame, Label

from bomb_configs import RPi, SHOW_BUTTONS


class Lcd(Frame):
    """Full-screen status display for the bomb game."""

    def __init__(self, window):
        super().__init__(window, bg="black")
        window.attributes("-fullscreen", True)
        self.pack(fill=BOTH, expand=True)
        self._timer = None
        self._button = None
        self.boot_frame = Frame(self, bg="black")
        self.boot_frame.grid(row=0, column=0, sticky="nw")
        self.bomb_frame = Frame(self, bg="black")
        self.bomb_frame.grid(row=1, column=0, sticky="nw")
        self._boot_index = 0

    def setup(self):
        """Create the live game status labels."""
        style = {"bg": "black", "fg": "#00ff00", "font": ("Courier New", 18)}
        self._ltimer = Label(self.bomb_frame, text="Time left:", **style)
        self._lkeypad = Label(self.bomb_frame, text="Keypad:", **style)
        self._lwires = Label(self.bomb_frame, text="Wires:", **style)
        self._lbutton = Label(self.bomb_frame, text="Button:", **style)
        self._ltoggles = Label(self.bomb_frame, text="Toggles:", **style)
        self._lstrikes = Label(self.bomb_frame, text="Strikes left:", **style)

        for row, widget in enumerate((
            self._ltimer, self._lkeypad, self._lwires,
            self._lbutton, self._ltoggles, self._lstrikes
        )):
            widget.grid(row=row, column=0, columnspan=3, sticky=W)

        if SHOW_BUTTONS:
            tkinter.Button(
                self.bomb_frame, text="Pause", bg="red", fg="white",
                font=("Courier New", 18), command=self.pause
            ).grid(row=6, column=0, pady=20)
            tkinter.Button(
                self.bomb_frame, text="Quit", bg="red", fg="white",
                font=("Courier New", 18), command=self.quit
            ).grid(row=6, column=2, pady=20)

    def setTimer(self, timer):
        self._timer = timer

    def setButton(self, button):
        self._button = button

    def pause(self):
        if RPi and self._timer is not None:
            self._timer.pause()

    def conclusion(self, success=False):
        for name in (
            "_ltimer", "_lkeypad", "_lwires", "_lbutton",
            "_ltoggles", "_lstrikes"
        ):
            widget = getattr(self, name, None)
            if widget is not None:
                widget.destroy()

        message = "BOMB DEFUSED!" if success else "BOOM! THE BOMB EXPLODED."
        color = "#39ff14" if success else "red"
        Label(
            self.bomb_frame, text=message, bg="black", fg=color,
            font=("Courier New", 26, "bold")
        ).grid(row=0, column=0, columnspan=3, pady=20)

        tkinter.Button(
            self.bomb_frame, text="Retry", bg="red", fg="white",
            font=("Courier New", 18), command=self.retry
        ).grid(row=1, column=0, pady=40)
        tkinter.Button(
            self.bomb_frame, text="Quit", bg="red", fg="white",
            font=("Courier New", 18), command=self.quit
        ).grid(row=1, column=2, pady=40)

    def retry(self):
        os.execv(sys.executable, [sys.executable, sys.argv[0]])

    def quit(self):
        if RPi:
            if self._timer is not None:
                self._timer.stop()
                self._timer._component.blink_rate = 0
                self._timer._component.fill(0)
            if self._button is not None:
                for pin in self._button._rgb:
                    pin.value = True
        self.winfo_toplevel().destroy()


class PhaseThread(Thread):
    """Base class for a hardware phase monitored by the main Tk thread."""

    def __init__(self, name, component=None, target=None):
        super().__init__(name=name, daemon=True)
        self._component = component
        self._target = target
        self._defused = False
        self._failed = False
        self._value = None
        self._running = False

    def stop(self):
        self._running = False


class Timer(PhaseThread):
    def __init__(self, component, initial_value, name="Timer"):
        super().__init__(name, component)
        self._value = max(0, int(initial_value))
        self._paused = False
        self._min = "00"
        self._sec = "00"

    def run(self):
        self._running = True
        while self._running and self._value > 0:
            if self._paused:
                sleep(0.1)
                continue
            self._update()
            self._component.print(str(self))
            sleep(1)
            if not self._paused and self._running:
                self._value -= 1

        self._value = max(0, self._value)
        self._update()
        if self._component is not None:
            self._component.print(str(self))
        self._running = False

    def _update(self):
        self._min = str(self._value // 60).zfill(2)
        self._sec = str(self._value % 60).zfill(2)

    def pause(self):
        self._paused = not self._paused
        self._component.blink_rate = 2 if self._paused else 0

    def __str__(self):
        return f"{self._min}:{self._sec}"


class Keypad(PhaseThread):
    def __init__(self, component, target, name="Keypad"):
        super().__init__(name, component, target)
        self._value = ""

    def run(self):
        self._running = True
        while self._running and not self._defused:
            pressed = self._component.pressed_keys
            if pressed:
                key = str(pressed[0])
                while self._running and self._component.pressed_keys:
                    sleep(0.05)
                if not self._running:
                    break
                self._value += key
                if self._value == self._target:
                    self._defused = True
                elif not self._target.startswith(self._value):
                    self._failed = True
            sleep(0.05)

    def __str__(self):
        return "DEFUSED" if self._defused else self._value


class Wires(PhaseThread):
    def run(self):
        self._running = True
        while self._running and not self._defused:
            states = [pin.value for pin in self._component]
            bit_string = "".join("1" if state else "0" for state in states)
            if int(bit_string[::-1], 2) == self._target:
                self._defused = True
            sleep(0.1)

    def __str__(self):
        if self._defused:
            return "DEFUSED"
        return "".join("1" if pin.value else "0" for pin in self._component)


class Button(PhaseThread):
    def __init__(self, component_state, component_rgb, target, color, timer, name="Button"):
        super().__init__(name, component_state, target)
        self._rgb = component_rgb
        self._color = color
        self._timer = timer
        self._pressed = False
        self._press_count = 0

    def run(self):
        self._running = True
        colors = {
            "R": (False, True, True),
            "G": (True, False, True),
            "B": (True, True, False),
        }
        for pin, value in zip(self._rgb, colors[self._color]):
            pin.value = value

        while self._running and not self._defused:
            is_pressed = bool(self._component.value)
            if is_pressed:
                self._pressed = True
            elif self._pressed:
                self._press_count += 1
                self._pressed = False
                if self._press_count >= 5:
                    self._defused = True
            sleep(0.05)

    def __str__(self):
        return "DEFUSED" if self._defused else f"Pressed {self._press_count} of 5 times"


class Toggles(PhaseThread):
    def run(self):
        self._running = True
        while self._running and not self._defused:
            bit_string = "".join(
                "1" if pin.value else "0" for pin in self._component
            )
            if int(bit_string, 2) == self._target:
                self._defused = True
            sleep(0.1)

    def __str__(self):
        if self._defused:
            return "DEFUSED"
        return "".join("1" if pin.value else "0" for pin in self._component)
