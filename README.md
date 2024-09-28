# Thread (Auto Core Binding Tool)

![project-image](https://raw.githubusercontent.com/upendraguptaoffice/Thread/main/Thread.png)

## Overview
This tool automates CPU core management, checks isolated cores, and assigns cores to run cells based on user input. It auto-converts core values to hexadecimal and updates the respective configuration files.

---

## Key Features

### Analyze CPU Information:
- Isolated physical and sibling cores.

### Auto-Check:
- For sufficient cores to run the selected number of cells.

### Core Value Conversion:
- Automatically assign and convert core values to hexadecimal.

### User Tweaks:
- Allows users to adjust core assignments before applying changes.

---

## Core Conversion Formula

**Total Sum = Σ (i=1 to k) 2^n<sub>i</sub>**

*Note: Where n<sub>i</sub> are the individual integer inputs provided by the user.*

---

## How to Use

**1. Install Prerequisites:**
Run `requirements.sh`.

**2. Run the Tool:**
Execute `python3 Thread.py`.

**3. Key Functions:**
- Show CPU Info
- Cells to Configure
- Core Alignment

All changes are saved in the files for future reference.

## 🚀 Demo

[DEMO](DEMO)

## Project Screenshots:

![project-screenshot](ss1 "Project Screenshot")

## 🧐 Features

Here're some of the project's best features:
- Show CPU Info
- Calculate Cells to Configure
- Auto Core Alignment

## 🛠️ Installation Steps:

1. Install Python:

    ```bash
    sudo apt update && sudo apt install python3 python3-pip -y && python3 --version && pip3 --version
    ```

2. Install Prerequisites:

    ```bash
    ./requirements.sh
    ```

3. Execute `Thread.py`:

    ```bash
    python3 Thread.py
    ```

## 💻 Built with

Technologies used in the project:
- Python
- Tkinter
- Bash Scripting
