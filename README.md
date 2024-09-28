<h1 align="center" id="title">Thread (Auto core binding tool)</h1>

<p align="center">
    <img src="https://raw.githubusercontent.com/upendraguptaoffice/Thread/main/Thread.png" alt="project-image" style="width: 25%;">
</p>

<p id="description"><meta charset="UTF-8"> <meta name="viewport" content="width=device-width initial-scale=1.0"> <title>Thread Core Binding Tool by Upendra</title> <style>body { font-family: Arial sans-serif; line-height: 1.6; margin: 20px; background-color: #f9f9f9; color: #333; } h1 { color: #2c3e50; } h2 { color: #2980b9; } h3 { color: #27ae60; } pre { background-color: #eef; padding: 10px; border: 1px solid #ccc; overflow-x: auto; } .feature { margin: 15px 0; padding: 10px; background-color: #ffffff; border: 1px solid #ddd; border-radius: 5px; } .note { font-style: italic; color: #666; }</style></p>

<h1>Thread Core Binding Tool by Upendra</h1>

<h2>Overview</h2>

<p>This tool automates CPU core management checks isolated cores and assigns cores to run cells based on user input. It auto-converts core values to hexadecimal and updates the respective configuration files.</p>

* * *

<h2>Key Features</h2>

### Analyze CPU Information:

*   Isolated physical and sibling cores.

### Auto-Check:

*   For sufficient cores to run the selected number of cells.

### Core Value Conversion:

*   Automatically assign and convert core values to hexadecimal.

### User Tweaks:

*   Allows users to adjust core assignments before applying changes.

* * *

<h2>Core Conversion Formula</h2>

<p><strong>Total Sum = Σ (i=1 to k) 2<sup>n<sub>i</sub></sup></strong></p>

<p class="note">*Where n<sub>i</sub> are the individual integer inputs provided by the user.*</p>

* * *

<h2>How to Use</h2>

<p>
    <strong><em>1. Install Prerequisites:</em></strong> <br>
    Run <code>requirements.sh</code>. <br><br>

    <strong><em>2. Run the Tool:</em></strong> <br>
    Execute <code>python3 Thread.py</code>. <br><br>

    <strong><em>3. Key Functions:</em></strong> <br>
    <ul>
        <li><code>Show CPU Info</code></li>
        <li><code>Cells to Configure</code></li>
        <li><code>Core Alignment</code></li>
    </ul>
</p>


<p>All changes are saved in the files for future reference.</p>

<h2>🚀 Demo</h2>

[DEMO](DEMO)

<h2>Project Screenshots:</h2>

<img src="ss1" alt="project-screenshot" width="ss2" height="ss3/">

  
  
<h2>🧐 Features</h2>

Here're some of the project's best features:

*   Show CPU Info
*   Calculate Cells to Configure
*   Auto Core Alignment

<h2>🛠️ Installation Steps:</h2>

<p>1. Install Python</p>

```
sudo apt update && sudo apt install python3 python3-pip -y && python3 --version && pip3 --version
```

<p>2. Install Prerequisites</p>

```
./requirements.sh
```

<p>3. Execute Thread.py</p>

```
python3 Thread.py
```

  
  
<h2>💻 Built with</h2>

Technologies used in the project:

*   Python
*   Tkinter
*   Bash Scripting
