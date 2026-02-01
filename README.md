# PSL Draft Simulator 🏏

A Flask-based PSL Draft Simulation System that allows teams to pick players under realistic PSL-style constraints such as budget limits, player categories, foreign player limits, and snake draft rounds.

This project is developed for **educational and academic purposes** and demonstrates the use of **Data Structures, File Handling, and Flask Web Development**.

---

## 🎯 Project Objective

To simulate the Pakistan Super League (PSL) draft process by enforcing:
- Budget limits
- Player category rules
- Foreign player limits
- Pre-draft and main draft phases
- Persistent data storage using CSV files

---

## 🧠 Concepts Used

### Data Structures
- **Queue (Deque)** – Draft order (snake draft)
- **Stack** – Undo draft operation
- **List & Set** – Team players and category constraints

### Programming Concepts
- Object-Oriented Programming (OOP)
- File Handling using CSV
- Flask routing and templates

---

## 👥 Features

### Admin
- Allocate team budgets
- Start the draft
- Reset application

### Teams
- Pre-draft up to 3 players
- Pick players in draft
- Budget and points validation
- Foreign player limit enforcement

### Draft System
- Snake draft order
- Category-based player sorting
- Undo and skip options

---

## 🏷 Player Categories

| Rating | Category |
|------|---------|
| > 90 | Platinum |
| 81 – 90 | Diamond |
| 61 – 80 | Silver |
| 51 – 60 | Bronze |
| ≤ 50 | Emerging |

---

## 🛠 Technologies Used

- Python 3
- Flask
- HTML / CSS
- CSV File Handling
- Queue, Stack, Sets

---

## 📂 Project Structure
PSL-Draft-Simulator/
|-- app.py
|-- data/
|   |-- players.csv
|   |-- teams.csv
|   |-- team_players.csv
|   |-- draft_state.csv
|-- templates/
|-- static/
|-- README.md
|-- RUN_INSTRUCTIONS.md

