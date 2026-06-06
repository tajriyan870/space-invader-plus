# Space Invaders+

> **Built for the Classic Game Replica Hackathon**
> IEEE Student Branch — SRH University of Applied Sciences, Leipzig
> June 6, 2026

---

## Developers

| Name | Institution |
|------|------------|
| Tajriyan Rahman | SRH University of Applied Sciences, Berlin |
| Panharith An | SRH University of Applied Sciences, Berlin |

---

## About the Game

**Space Invaders+** is a faithful recreation of the 1978 Atari arcade classic — reimagined with modern twists including local co-op multiplayer, gravity physics, charge shots, and evolving alien mutations.

Built entirely in **Python + Pygame**, exportable to browser via **Pygbag**.

---

## Features

### Core (faithful to the original)
- Classic alien grid — 4 rows × 10 columns with 3 distinct alien types (squid, crab, octopus)
- Aliens march sideways, drop down, and speed up as their numbers fall
- Destructible shields that degrade block by block when hit
- Lives system, wave progression, and score tracking
- Aliens fire back — and aim more accurately on higher waves

### Added Features (our creative pivots)

| Feature | Description |
|---------|-------------|
| **Local Co-op Multiplayer** | Two players share one keyboard and compete on the same alien grid simultaneously |
| **Gravity Wave** | A periodic shockwave pulses across the screen every ~20 seconds, bending all bullets mid-flight. A flashing warning line appears beforehand so you can prepare |
| **Charge Shot** | Hold the Shift key to charge up a powerful blast — fully charged deals 4× damage and can one-shot even the toughest aliens |
| **Alien Mutations** | From wave 3 onwards, aliens gain more HP and start aiming directly at players instead of shooting randomly |
| **Score Duel** | Both players compete individually — the player with the higher score at game over is declared the winner |
| **Sound Effects** | Fully synthesized audio (no external files) — shoot sounds, alien hits, explosions, gravity booms, wave clears |

---

## Controls

| Action | Player 1 | Player 2 |
|--------|----------|----------|
| Move Left | `A` | Left Arrow |
| Move Right | `D` | Left Arrow |
| Fire | `SPACE` | `ENTER` |
| Charge Shot | Hold `L-SHIFT` | Hold `R-SHIFT` |

### General
| Key | Action |
|-----|--------|
| `ESC` | Pause / Quit to main menu |
| UP / DOWN | Navigate main menu |

### Cheat Codes
| Code | Effect |
|------|--------|
| Press `V` three times | Refill Player 1 lives to 3 |
| Press `P` three times | Refill Player 2 lives to 3 |

---

## How to Run

### Requirements
```
Python 3.10 or 3.11 recommended (not 3.13)
```

### Install dependencies
```bash
pip install -r requirements.txt
```

### Run the game
```bash
python main.py
```

### Export to browser (for sharing)
```bash
pygbag .
```
Then open `http://localhost:8000` — works in any modern browser, no install needed for players.

---

## Project Structure

```
space-invaders-plus/
├── main.py            <- entire game (single file, ~1000 lines)
├── requirements.txt   <- pygame, pygbag, numpy
└── README.md          <- this file
```

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.11 | Core language |
| Pygame | Game engine, rendering, input |
| NumPy | Procedural sound synthesis |
| Pygbag | WebAssembly export for browser play |

> All sounds are generated procedurally at runtime using NumPy — no audio files required.

---

## Hackathon Context

This project was built in one day for the **Classic Game Replica Hackathon**, the first ever event organised by the **IEEE Student Branch at SRH University of Applied Sciences Leipzig**.

**Event details:**
- Date: Saturday, June 6, 2026
- Time: 13:00 – 18:30
- SRH University of Applied Sciences, Leipzig
- AI tools were allowed and encouraged

**Judging criteria:**
- Size & bite of the game
- Sprite & feature complexity
- Number of features pivoted from the original idea
- Creativity
- Crowd vote

---

## Original Game Credit

Space Invaders was originally created by **Tomohiro Nishikado** and released by **Taito** in 1978.
This project is a non-commercial fan recreation built for educational and hackathon purposes.

---

*Made with love and way too much caffeine — SRH Leipzig, 2026*
