# Defuse the Bomb — Mathematical Meltdown

A Python and Raspberry Pi hardware game created for **CSC 102** by **Kobe and Lucas**. Players have five minutes to solve four hardware challenges before the countdown reaches zero. Incorrect keypad entries use up the available strikes.

## Features

- Five-minute countdown shown on a four-digit I2C 7-segment display
- Full-screen Tkinter status display, boot sequence, and end-game screen
- Matrix keypad combination challenge
- Five-wire binary pattern challenge
- Four-toggle binary pattern challenge
- RGB pushbutton challenge requiring five complete press-and-release cycles
- Five-strike limit
- Optional background music and explosion sound effects
- Separate worker threads for the timer and hardware input phases
- Windows test mode that does not import Raspberry Pi-only libraries

## Project files

```text
Bomb-Project/
├── bomb.py             # Application startup, game loop, strikes, and results
├── bomb_configs.py     # Hardware setup, settings, and puzzle targets
├── bomb_phases.py      # Tkinter interface and phase-thread classes
├── requirements.txt    # Python dependencies
├── Bomb.mp3            # Optional background music (not included)
├── Explosion.mp3       # Optional explosion sound (not included)
└── README.md
```

## Hardware configuration

The hardware configuration expects a Raspberry Pi with these components:

| Component | GPIO pins |
|---|---|
| 7-segment display | I2C (SDA/SCL) |
| Matrix keypad columns | GPIO 10, 9, 11 |
| Matrix keypad rows | GPIO 5, 6, 13, 19 |
| Jumper wires | GPIO 14, 15, 18, 23, 24 |
| Pushbutton input | GPIO 4 |
| RGB LED | GPIO 17, 27, 22 |
| Toggle switches | GPIO 12, 16, 20, 21 |

Use the wiring diagram and pinout supplied with the class project. Confirm all connections before powering the Raspberry Pi.

## Puzzle targets

| Phase | Required input |
|---|---|
| Keypad | `235` |
| Wires | Binary pattern `00100` (decimal target 4; bit order is reversed in the phase logic) |
| Toggles | Binary pattern `1100` (decimal target 12) |
| Pushbutton | Five full press-and-release cycles |

The button LED color is selected randomly. The current button challenge uses five presses; the serial-number-derived button target is retained in configuration but is not used by the current button logic.

## Run on Windows (GUI/test mode)

The repository defaults to `RPi = False` in `bomb_configs.py`. This allows the application to start without importing Raspberry Pi GPIO libraries.

1. Install Python 3.
2. Open PowerShell in the project folder.
3. Install optional audio support if desired:

   ```powershell
   python -m pip install pygame
   ```

4. Start the application:

   ```powershell
   python bomb.py
   ```

In Windows test mode, the GUI displays a notice that hardware gameplay is disabled. Physical phases are not simulated. Press **Escape** to close the full-screen window.

## Run on Raspberry Pi

1. Set `RPi = True` near the top of `bomb_configs.py`.
2. Enable I2C and configure GPIO access in Raspberry Pi OS.
3. Install dependencies:

   ```bash
   python3 -m pip install -r requirements.txt
   sudo apt install python3-tk
   ```

4. Run from the project directory:

   ```bash
   python3 bomb.py
   ```

The audio files are optional. Place `Bomb.mp3` and `Explosion.mp3` beside `bomb.py` to enable sound. If pygame or either audio file is unavailable, the application continues without audio.

## Configuration

- `RPi` — `False` for Windows testing; `True` on the configured Raspberry Pi
- `COUNTDOWN` — starting time in seconds
- `NUM_STRIKES` — incorrect keypad entries allowed
- `SHOW_BUTTONS` — whether Pause and Quit controls appear in the live interface

Math trivia question data is retained in `genMathQuestions()`, but it is not currently presented as an interactive trivia stage by the main program.

## Notes

- Hardware behavior must be tested on the actual Raspberry Pi before demonstration.
- GPIO pin order and physical wiring must match the configuration above.
- This is a class team project by Kobe and Lucas.
