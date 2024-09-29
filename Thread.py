import subprocess
import tkinter as tk
import os
import re
import time
from PIL import Image, ImageTk
from tkinter import simpledialog, messagebox, scrolledtext


# Function to run shell commands
def run_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

# Function to check hyperthreading
def check_hyperthreading():
    threads_per_core = run_command("lscpu | grep -E '^Thread\\(s\\) per core:' | awk '{print $4}'")
    return "Enabled" if threads_per_core == "2" else "Disabled"

# Function to parse core list
def parse_core_list(core_list):
    cores = []
    for part in core_list.split(','):
        # Strip any extra whitespace, newline characters, or other hidden characters
        part = part.strip().replace('\n', '')
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
                cores.extend(range(start, end + 1))
            except ValueError:
                print(f"Invalid range: {part}")
        else:
            try:
                cores.append(int(part))
            except ValueError:
                print(f"Invalid core value: {part}")
    return cores

# Function to check NUMA nodes
def check_numa_nodes():
    numa_output = run_command("lscpu")
    numa_dict = {}
    in_numa_section = False

    result = ""
    for line in numa_output.splitlines():
        line = line.strip()
        if line.startswith("NUMA node"):
            in_numa_section = True
            parts = line.split()
            node_id = parts[1].replace("node", "")
            cores = parts[-1]
            cores_expanded = parse_core_list(cores)
            numa_dict[node_id] = cores_expanded
            result += f"CPU(s): {', '.join(map(str, cores_expanded))}\n"
        elif in_numa_section and not line.startswith("NUMA"):
            break

    if not numa_dict:
        result = "No NUMA nodes found."

    return result, numa_dict

# Function to check isolated cores
def check_isolated_cores():
    isolated_cores = run_command("cat /proc/cmdline | grep -o '\\<rcu_nocbs=[^ ]*\\>' | cut -d'=' -f2")
    return isolated_cores

# Function to identify isolated and sibling cores
def identify_isolated_and_sibling_cores(isolated_core_str, numa_dict):
    isolated_cores = parse_core_list(isolated_core_str)
    result_physical = ""
    result_sibling = ""

    isolated_cores_set = set(isolated_cores)
    for node, cores_list in numa_dict.items():
        mid_point = len(cores_list) // 2
        physical_cores = cores_list[:mid_point]
        sibling_cores = cores_list[mid_point:]

        numa_isolated_physical = [core for core in physical_cores if core in isolated_cores_set]
        numa_isolated_sibling = [core for core in sibling_cores if core in isolated_cores_set]

        if numa_isolated_physical:
            result_physical += f"{', '.join(map(str, numa_isolated_physical))}\n"
        if numa_isolated_sibling:
            result_sibling += f"{', '.join(map(str, numa_isolated_sibling))}\n"

    return result_physical, result_sibling

# Function to save information to cpu_info.txt
def save_to_file(hyperthreading_status, numa_result, physical_cores, sibling_cores, isolated_cores_str, cells):
    with open("cpu_info.txt", "w") as file:
        file.write(f"Hyperthreading Status: {hyperthreading_status}\n")
        file.write(f"NUMA Nodes Information:\n{numa_result}\n")
        file.write(f"Isolated Cores: {isolated_cores_str}\n")
        file.write(f"Physical Cores: {physical_cores.strip()}\n")
        file.write(f"Sibling Cores: {sibling_cores.strip()}\n")
        file.write(f"Number of Cells to Run: {cells}\n")

# Function to display the result in a structured format
# Global variable to store selected number of cells
selected_cells = None

# Function to display the result in a structured format
def run_checks():
    global selected_cells
    numa_label.delete(1.0, tk.END)
    physical_label.delete(1.0, tk.END)
    sibling_label.delete(1.0, tk.END)

    isolated_cores_str = check_isolated_cores()
    numa_result, numa_dict = check_numa_nodes()
    hyperthreading_status = check_hyperthreading()
    physical_cores, sibling_cores = identify_isolated_and_sibling_cores(isolated_cores_str, numa_dict)

    isolated_label.config(text=isolated_cores_str)
    numa_label.insert(tk.END, numa_result)
    hyper_label.config(text=f"{hyperthreading_status}")
    physical_label.insert(tk.END, f"{physical_cores.strip()}")
    sibling_label.insert(tk.END, f"{sibling_cores.strip()}")

    # Save the information to cpu_info.txt after cell selection
    ask_for_cells(hyperthreading_status, numa_result, physical_cores, sibling_cores, isolated_cores_str)
    # Proceed to core binding
    # ask_for_core_binding()

# Function to handle cell selection
def ask_for_cells(hyperthreading_status, numa_result, physical_cores, sibling_cores, isolated_cores_str):
    global selected_cells
    cells = simpledialog.askinteger("Cell Selection", "How many cells do you want to run (1-4)?", minvalue=1, maxvalue=4)
    if cells is not None:
        selected_cells = cells  # Store the selected number of cells
        # Check isolated cores based on the number of cells
        isolated_cores_count = len(parse_core_list(isolated_cores_str))
        
        if cells == 1 and isolated_cores_count >= 22:
            messagebox.showinfo("Cell Selection", "You can run 1 cell.")
        elif cells == 2 and isolated_cores_count >= 28:
            messagebox.showinfo("Cell Selection", "You can run 2 cells.")
        elif cells == 3 and isolated_cores_count >= 34:
            messagebox.showinfo("Cell Selection", "You can run 3 cells.")
        elif cells == 4 and isolated_cores_count >= 40:
            messagebox.showinfo("Cell Selection", "You can run 4 cells.")
        else:
            messagebox.showerror("Cell Selection", "Not enough isolated cores to run the selected number of cells.")
        
        # Proceed to save information including the number of cells
        save_to_file(hyperthreading_status, numa_result, physical_cores, sibling_cores, isolated_cores_str, selected_cells)
    else:
        messagebox.showwarning("Cell Selection", "Cell selection was cancelled.")
       


def ask_for_core_binding():
    file_name = "core_binding_paths.txt"
    
    # Initialize variables for paths
    l1_dir = ""
    gnb_cu_dir = ""
    gnb_du_dir = ""

    # Check if the file exists
    if os.path.exists(file_name):
        # Read paths from the file
        with open(file_name, "r") as file:
            lines = file.readlines()
            l1_dir = lines[0].split(": ", 1)[1].strip()
            gnb_cu_dir = lines[1].split(": ", 1)[1].strip()
            gnb_du_dir = lines[2].split(": ", 1)[1].strip()
    
    # Prepopulate the dialog boxes with the existing paths (or empty if they don't exist)
    l1_path = simpledialog.askstring("L1 Path", "Enter the L1 Path:", initialvalue=l1_dir.replace("l1/", ""))
    gnb_path = simpledialog.askstring("gNB Path", "Enter the gNB Path:", initialvalue=gnb_cu_dir.replace("cfg", ""))

    # Validate the input and update the paths
    if l1_path and gnb_path:
        l1_dir = f"{l1_path}l1/"
        gnb_cu_dir = f"{gnb_path}cu_cfg"
        gnb_du_dir = f"{gnb_path}du_cfg"

        # Show the entered paths
        messagebox.showinfo("Core Binding", f"L1 Path Directory: {l1_dir}\n"
                                             f"gNB CU Path Directory: {gnb_cu_dir}\n"
                                             f"gNB DU Path Directory: {gnb_du_dir}")
        
        # Save the updated paths to the file
        with open(file_name, "w") as file:
            file.write(f"L1_Path_Directory: {l1_dir}\n")
            file.write(f"gNB_CU_Path_Directory: {gnb_cu_dir}\n")
            file.write(f"gNB_DU_Path_Directory: {gnb_du_dir}\n")
            
        # Return the paths for use in other functions
        return {
            "l1_dir": l1_dir,
            "gnb_cu_dir": gnb_cu_dir,
            "gnb_du_dir": gnb_du_dir
        }
    else:
        messagebox.showwarning("Core Binding", "Path input was cancelled or invalid.")
        return None


# Function to show all CPU info
def show_cpu_info():
    isolated_cores_str = check_isolated_cores()
    numa_result, numa_dict = check_numa_nodes()
    hyperthreading_status = check_hyperthreading()
    physical_cores, sibling_cores = identify_isolated_and_sibling_cores(isolated_cores_str, numa_dict)

    isolated_label.config(text=isolated_cores_str)
    numa_label.delete(1.0, tk.END)
    numa_label.insert(tk.END, numa_result)
    hyper_label.config(text=f"{hyperthreading_status}")
    physical_label.delete(1.0, tk.END)
    physical_label.insert(tk.END, f"{physical_cores.strip()}")
    sibling_label.delete(1.0, tk.END)
    sibling_label.insert(tk.END, f"{sibling_cores.strip()}")

def extract_and_overwrite_cpu_info(file_path):
    # First check if the exact line "CPU(s): 1" exists in the file
    with open(file_path, 'r') as file:
        lines = file.readlines()
        # Check for the exact match of "CPU(s): 1"
        if any(line.strip() == "CPU(s): 1" for line in lines):
            print("Skipping execution: Exact 'CPU(s): 1' found in the file.")
            return  # Exit the function if the exact line "CPU(s): 1" is found

    # If the exact line "CPU(s): 1" is not found, proceed with processing
    data = {
        'Hyperthreading Status': '',
        'NUMA Nodes Information': [],
        'Isolated Cores': '',
        'Physical Cores': '',
        'Sibling Cores': '',
        'Number of Cells to Run': ''
    }

    # Re-open the file for further processing
    with open(file_path, 'r') as file:
        for idx, line in enumerate(lines):
            line = line.strip()

            if line.startswith("Hyperthreading Status:"):
                data['Hyperthreading Status'] = line.split(": ")[1]

            # Collect all lines starting with "CPU(s):" under NUMA Nodes Information, skipping "CPU(s): 2"
            if line.startswith("CPU(s):"):
                cpu_line = line.split(": ")[1]
                if cpu_line != "2":  # Skip "CPU(s): 2"
                    data['NUMA Nodes Information'].append(cpu_line)

            if line.startswith("Isolated Cores:"):
                data['Isolated Cores'] = line.split(": ")[1]

            if line.startswith("Physical Cores:"):
                # Store the current line and check for the next line
                if idx + 1 < len(lines):
                    data['Physical Cores'] = lines[idx + 1].strip()  # Get the next line

            if line.startswith("Sibling Cores:"):
                # Store the current line and check for the next two lines
                if idx + 2 < len(lines):
                    data['Sibling Cores'] = lines[idx + 2].strip()  # Get the next two lines

            if line.startswith("Number of Cells to Run:"):
                data['Number of Cells to Run'] = line.split(": ")[1]

    # Prepare the output string
    output = []
    output.append(f"Hyperthreading Status: {data['Hyperthreading Status']}\n")
    output.append("NUMA Nodes Information:\n")
    for cpu in data['NUMA Nodes Information']:
        output.append(f"CPU(s): {cpu}\n")
    output.append(f"Isolated Cores: {data['Isolated Cores']}\n")
    output.append(f"Physical Cores: {data['Physical Cores']}\n")
    output.append(f"Sibling Cores: {data['Sibling Cores']}\n")
    output.append(f"Number of Cells to Run: {data['Number of Cells to Run']}\n")

    # Overwrite the file with the updated content
    with open(file_path, 'w') as file:
        file.writelines(output)

    print("File has been processed successfully!")


# Function to handle core alignment input
def do_core_alignment_pre():
        # Specify the file path
    file_path = 'cpu_info.txt'

    # Extract and overwrite the information while skipping "CPU(s): 2"
    extract_and_overwrite_cpu_info(file_path)

    print("File has been processed successfully!")

    # Function to parse CPU information
    def parse_cpu_info(file):
        cpu_info = {}
        with open(file, 'r') as f:
            for line in f:
                if 'Hyperthreading Status' in line:
                    cpu_info['Hyperthreading'] = 'Enabled' if 'Enabled' in line else 'Disabled'
                elif 'CPU(s):' in line:
                    cpu_list = list(map(int, re.findall(r'\d+', line)))
                    if 'NUMA Nodes Information' in cpu_info:
                        cpu_info['NUMA Nodes'].append(cpu_list)
                    else:
                        cpu_info['NUMA Nodes'] = [cpu_list]
                elif 'Isolated Cores:' in line:
                    cpu_info['Isolated Cores'] = list(map(int, re.findall(r'\d+', line)))
                elif 'Physical Cores:' in line:
                    cpu_info['Physical Cores'] = list(map(int, re.findall(r'\d+', line)))
                elif 'Sibling Cores:' in line:
                    cpu_info['Sibling Cores'] = list(map(int, re.findall(r'\d+', line)))
                elif 'Number of Cells to Run:' in line:
                    cpu_info['Cells'] = int(re.search(r'\d+', line).group())
        return cpu_info

    # Function to generate core alignment
    def generate_core_alignment(cpu_info, l1_dir, gnb_cu_dir, gnb_du_dir):
        # Extract necessary information
        physical_cores = cpu_info['Physical Cores']
        sibling_cores = cpu_info['Sibling Cores']
        num_cells = cpu_info['Cells']

        # Rule-based thread-core mapping with dynamic paths
        core_allocation = [
            ("L1_core1,L1_core2,L1_core3", f"{l1_dir}/l1_cfg", physical_cores[0]),
            ("DU_core1,DU_core2,DU_core3", f"{gnb_du_dir}/du_cfg", sibling_cores[0]),
            ("CU_core1,CU_core2,CU_core3", f"{gnb_du_dir}/cu_cfg", sibling_cores[0]),
            ("OAM_core1,OAM_core2,OAM_core3", f"{l1_dir}/oam_cfg", physical_cores[1]),
            ("O1_core1,O1_core2,O1_core3", f"{l1_dir}/o1_cfg", sibling_cores[1]),
            ("F1_core1,F1_core2,F1_core3", f"{gnb_du_dir}/f1_cfg", physical_cores[2]),
            ("PHY_core1,PHY_core2,PHY_core3", f"{gnb_du_dir}/phy_cfg", physical_cores[2]),
            ("PDCP_core1,PDCP_core2,PDCP_core3", f"{gnb_du_dir}/pdcp_cfg", sibling_cores[2]),
            ("RLC_core1,RLC_core2,RLC_core3", f"{gnb_du_dir}/rlc_cfg", sibling_cores[2]),
            ("MAC_core1,MAC_core2,MAC_core3", f"{gnb_du_dir}/mac_cfg", physical_cores[3]),
        ]

        # Additional rules for cells
        if num_cells == 1:
            core_allocation.append(("bbu", f"{l1_dir}/l1_cfg", physical_cores[6], sibling_cores[6]))
            core_allocation.append(("maclow", f"{gnb_du_dir}/du_cfg", physical_cores[7]))
            core_allocation.append(("mactx", f"{gnb_du_dir}/du_cfg", sibling_cores[7]))
        elif num_cells == 2:
            core_allocation.append(("bbu", f"{l1_dir}/l1_cfg", physical_cores[6:9], sibling_cores[6:9]))
            core_allocation.append(("maclow", f"{gnb_du_dir}/du_cfg", physical_cores[9:11]))
            core_allocation.append(("mactx", f"{gnb_du_dir}/du_cfg", sibling_cores[9:11]))
        elif num_cells == 3:
            core_allocation.append(("bbu", f"{l1_dir}/l1_cfg", physical_cores[6:11], sibling_cores[6:11]))
            core_allocation.append(("maclow", f"{gnb_du_dir}/du_cfg", physical_cores[11:14]))
            core_allocation.append(("mactx", f"{gnb_du_dir}/du_cfg", sibling_cores[11:14]))
        elif num_cells == 4:
            core_allocation.append(("bbu", f"{l1_dir}/l1_cfg", physical_cores[6:12], sibling_cores[6:12]))
            core_allocation.append(("maclow", f"{gnb_du_dir}/du_cfg", physical_cores[12:16]))
            core_allocation.append(("mactx", f"{gnb_du_dir}/du_cfg", sibling_cores[12:16]))

        return core_allocation

    # Function to export core alignment to a file
    def export_core_alignment(filename, core_allocation):
        with open(filename, 'w') as f:
            for allocation in core_allocation:
                if len(allocation) == 3:  # Only physical cores
                    thread_names, file_name, cores = allocation
                    if isinstance(cores, list):  # If cores are in a list, join them
                        cores = ','.join(map(str, cores))
                    f.write(f"{thread_names} {file_name} {cores}\n")
                elif len(allocation) == 4:  # Both physical and sibling cores
                    thread_names, file_name, cores, sibling_cores = allocation
                    if isinstance(cores, list):  # Join core list to a string
                        cores = ','.join(map(str, cores))
                    if isinstance(sibling_cores, list):  # Join sibling cores list to a string
                        sibling_cores = ','.join(map(str, sibling_cores))
                    f.write(f"{thread_names} {file_name} {cores},{sibling_cores}\n")


    # Main execution
    if __name__ == "__main__":
        # Read cpu_info.txt
        cpu_info = parse_cpu_info('cpu_info.txt')

         # Get the paths using ask_for_core_binding()
        paths = ask_for_core_binding()

        # Check if paths were successfully retrieved
        if paths:
            # Generate core alignment based on the rules, using the paths
            core_allocation = generate_core_alignment(cpu_info, paths['l1_dir'], paths['gnb_cu_dir'], paths['gnb_du_dir'])

            # Export the alignment to Core_Alignment.txt
            export_core_alignment('Core_Alignment.txt', core_allocation)

            print("Core alignment successfully exported to Core_Alignment.txt")
        else:
            print("Core alignment process cancelled or paths were invalid.")


# Function to handle core alignment input
def do_core_alignment():
    do_core_alignment_pre()
    # Create a top-level window for core alignment
    alignment_window = tk.Toplevel()
    alignment_window.title("Core Alignment")
    alignment_window.geometry("1080x600")

    # Function to read data from Core_Alignment.txt file
    def read_core_alignment_file():
        alignment_data = []
        with open("Core_Alignment.txt", "r") as file:
            for line in file.readlines():
                parts = line.strip().split()
                if len(parts) >= 3:
                    threads = parts[0]
                    filename = parts[1]
                    cores = " ".join(parts[2:])
                    alignment_data.append((threads, filename, cores))
        return alignment_data

    # Load alignment data from the file
    alignment_data = read_core_alignment_file()

    # Dictionary to store entry widgets for core numbers
    core_entries = []

    # Create a scrollable frame to hold the data
    scroll_frame = tk.Frame(alignment_window)
    scroll_frame.pack(fill="both", expand=True)

    canvas = tk.Canvas(scroll_frame)
    scrollbar = tk.Scrollbar(scroll_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Loop through each alignment entry and create labels/entry fields
    for i, (threads, filename, cores) in enumerate(alignment_data):
        # Thread names (non-editable)
        thread_label = tk.Label(scrollable_frame, text=f"{threads}", font=("Arial", 10, "bold"))
        thread_label.grid(row=i, column=0, padx=10, pady=5, sticky="w")

        # Filename (hidden, but stored)
        filename_hidden = tk.Label(scrollable_frame, font=("Arial", 10))
        filename_hidden.grid(row=i, column=1, padx=10, pady=5, sticky="w")

        # Cores (editable)
        core_entry = tk.Entry(scrollable_frame, font=("Arial", 10))
        core_entry.insert(0, cores)  # Pre-fill with the current core numbers
        core_entry.grid(row=i, column=2, padx=10, pady=5, sticky="w")
        core_entries.append((threads, filename, core_entry))

    # Function to save the edited core alignment data to a text file
    def save_core_alignment():
        with open("Core_Alignment.txt", "w") as file:
            for threads, filename, entry in core_entries:
                file.write(f"{threads} {filename} {entry.get()}\n")
        implement_core_binding()
        alignment_window.destroy()  # Close the window after saving

    # OK button to trigger save
    ok_button = tk.Button(alignment_window, text="OK", command=save_core_alignment, font=("Arial", 12), bg="#43A047", fg="white")
    ok_button.pack(pady=10)

#Function to implement the corebinding
def implement_core_binding():
    # Function to convert a list of cores into a hex string (e.g., 4,5,6,7 -> 6000000F0)
    def convert_cores_to_hex(cores):
        # Convert each core to its corresponding bit position, sum them, and then convert to hex
        core_mask = sum(2**int(core) for core in cores)
        return f'{core_mask:X}'

    # Function to handle core number replacement for the first group of threads
    def replace_first_core_number(thread, core_number, cores):
        print(f"Original cores for {thread}: {cores}")
        cores[0] = str(core_number)  # Replace only the first core number
        print(f"Updated cores for {thread}: {cores}")
        return f'<{thread}>{", ".join(cores)}</{thread}>'

    # Function to handle core number replacement for specific threads with '=' rule (no conversion for specified threads)
    def replace_core_number_after_equal(thread, core_number, content):
        print(f"Replacing {thread} core number with: {core_number}")
        pattern = re.compile(rf'\b{thread}=\d*')

        def process_match(match):
            return f'{thread}={core_number}'

        return pattern.sub(process_match, content)

    # Function to handle xRANWorker-specific rule
    def update_xranworker_core(thread, cores, content):
        hex_core = convert_cores_to_hex(cores)
        print(f"Converted cores {cores} to hex: {hex_core}")

        pattern = re.compile(rf'<{thread}>0x(\w+), ([\d, ]+)</{thread}>')

        def process_match(match):
            return f'<{thread}>0x{hex_core}, {match.group(2)}</{thread}>'

        return pattern.sub(process_match, content)

    # Function to handle BbuPoolThreadDefault_0_63-specific rule
    def update_bbupoolthread_core(thread, cores, content):
        hex_core = convert_cores_to_hex(cores)
        print(f"Converted cores {cores} to hex: {hex_core}")

        pattern = re.compile(rf'<{thread}>0x(\w+)</{thread}>')

        def process_match(match):
            return f'<{thread}>0x{hex_core}</{thread}>'

        return pattern.sub(process_match, content)

    # Function to handle the general case for any threadname with '=' format (conversion)
    def update_generic_thread_core(thread, cores, content):
        hex_core = convert_cores_to_hex(cores)
        print(f"Converted cores {cores} to hex: {hex_core}")

        pattern = re.compile(rf'\b{thread}=\w+')

        def process_match(match):
            return f'{thread}={hex_core}'

        return pattern.sub(process_match, content)

    # Function to handle different rules for different threads
    def update_core_number(xml_file, cores, threadnames):
        try:
            print(f"Processing file: {xml_file} with cores: {cores} for threads: {threadnames}")

            with open(xml_file, 'r') as file:
                content = file.read()

            # Loop through each threadname and apply the corresponding rule
            for thread in threadnames:
                core_list = cores.split(',') if ',' in cores else [cores]
                if thread in ['bin']:
                    content = replace_core_number_after_equal(thread, core_list[0], content)
                elif thread in ['systemmThreads']:
                    pattern = re.compile(rf'<{thread}>\s*([\d,\s]+)\s*</{thread}>')

                    def process_match(match):
                        core_numbers = [core.strip() for core in match.group(1).split(',')]
                        return replace_first_core_number(thread, core_list[0], core_numbers)

                    content = pattern.sub(process_match, content)
                elif thread == 'RANWorker':
                    content = update_xranworker_core(thread, core_list, content)
                elif thread == 'bbu':
                    content = update_bbupoolthread_core(thread, core_list, content)
                else:
                    content = update_generic_thread_core(thread, core_list, content)

            with open(xml_file, 'w') as file:
                file.write(content)

            print(f"Updated {xml_file} with cores {cores} for threads: {threadnames}")
        except Exception as e:
            print(f"Error updating {xml_file}: {e}")

    # Read the text file and process each line
    def process_file(input_file):
        try:
            with open(input_file, 'r') as file:
                for line in file:
                    if line.strip():  
                        parts = line.strip().split()
                        if len(parts) == 3:
                            threadnames = parts[0].split(',')
                            filename = parts[1]
                            cores_to_change = parts[2]
                            
                            print(f"Read line: {line.strip()}")
                            update_core_number(filename, cores_to_change, threadnames)
                        else:
                            print(f"Invalid line format: {line.strip()}")
        except Exception as e:
            print(f"Error reading {input_file}: {e}")

    # Replace 'upgraded_input.txt' with the path to your text file
    process_file('Core_Alignment.txt')

class info:
    def __init__(self, root):
        self.root = root
        self.root.title("INFO")
        self.root.geometry("1024x900")
        self.root.config(bg="#f4f4f4")

        # Title
        title_label = tk.Label(self.root, text="Thread \n Core Binding Tool by Upendra", font=("Arial", 24, "bold"), bg="#34495e", fg="white", pady=10)
        title_label.pack(fill="x")

        # Overview Section
        self.create_section("Overview", 
                            "This tool automates CPU core management, checks isolated cores,\n"
                            "and assigns cores to run cells based on user input. It auto-converts core values \n "
                            "to hexadecimal and updates the respective configuration files.", "#f39c12")

        # Features Section
     
        # Key Features Section
        self.create_section(
            "Key Features", 
            " - Analyze CPU information: isolated, physical, and sibling cores.\n"
            " - Auto-check for sufficient cores to run the selected number of cells.\n"
            " - Automatically assign and convert core values to hex.\n"
            " - Allows users to tweak core assignments before applying.", 
            "#3498db"
        )

        # Core Conversion Formula Section
        self.create_section(
            "Core Conversion Formula", 
            "Total Sum = Sigma (i=1 to k) 2^(n_i)\n"
            "where n_i are the individual integer inputs provided by the user.\n\n" , "#2ecc71"
        )

        # How to Use Section
        self.create_section(
            "How to Use", 
            "1. Install the prerequisites by running requirements.sh.\n"
            "2. Run the tool: python3 Thread.py\n"
            "3. Key functions:\n"
            "  - Show CPU Info\n"
            "  - Cells to Configure\n"
            "  - Core Alignment\n"
            "All changes are saved in the files for future reference.", 
            "#e74c3c"
        )
        # # Exit Button
        # exit_button = tk.Button(self.root, text="Exit", command=self.root.quit, font=("Arial", 14), bg="#e74c3c", fg="white", padx=20, pady=10)
        # exit_button.pack(pady=20)

    def create_section(self, title, content, bg_color):
        # Section frame
        frame = tk.Frame(self.root, bg=bg_color, padx=10, pady=10)
        frame.pack(fill="x", padx=20, pady=10)

        # Section title
        section_title = tk.Label(frame, text=title, font=("Arial", 18, "bold"), bg=bg_color, fg="white", anchor="w")
        section_title.pack(fill="x")

        # Section content
        section_content = tk.Label(frame, text=content, font=("Arial", 12), bg=bg_color, fg="white", justify="left", anchor="w")
        section_content.pack(fill="x")

def info_main():
    # Create the main window
    root = tk.Tk()
    app = info(root)
    root.mainloop()

# Function to close the window after 5 seconds
def close_window(root):
    time.sleep(5)
    root.quit()
    root.destroy()

# Create the main window
root = tk.Tk()
root.title("Thread By Upendra")


# Set the window size to 600x600
window_width = 600
window_height = 600

# Get the screen width and height
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Calculate the center position
x_position = (screen_width // 2) - (window_width // 2)
y_position = (screen_height // 2) - (window_height // 2)

# Set the geometry of the window to open it in the center
root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

# Load and resize the image to fit within 600x600
image = Image.open("Thread.png")
image = image.resize((600, 600), Image.Resampling.LANCZOS)  # Updated to use LANCZOS
photo = ImageTk.PhotoImage(image)

# Create a label to display the image
label = tk.Label(root, image=photo)
label.pack()

# Start the timer for 5 seconds and close the window
root.after(100, lambda: close_window(root))

# Start the Tkinter event loop
root.mainloop()

# Create the GUI window
window = tk.Tk()
window.title("Thread By Upendra")
window.geometry("1080x600")
window.config(bg="#E8F5E9")

# Create a frame to hold both the title label and the info button
top_frame = tk.Frame(window, bg="#43A047")
top_frame.pack(fill="x", pady=10, padx=20)

# Title Label (aligned to the left)
title_label = tk.Label(top_frame, text="CPU Information", font=("Arial", 16, "bold"), bg="#43A047", fg="white")
title_label.pack(side=tk.LEFT)

# Info Button (aligned to the right)
alignment_button = tk.Button(top_frame, text="INFO", command=info_main, font=("Arial", 12), bg="#43A047", fg="white")
alignment_button.pack(side=tk.RIGHT)


# Create frames for each section
isolated_frame = tk.Frame(window, bg="#A5D6A7", bd=2, relief="groove")
isolated_frame.pack(fill="x", padx=20, pady=5)
isolated_title = tk.Label(isolated_frame, text="Isolated Cores", font=("Arial", 12, "bold"), bg="#A5D6A7")
isolated_title.pack(anchor="w")
isolated_label = tk.Label(isolated_frame, text="", font=("Arial", 12), bg="#A5D6A7")
isolated_label.pack(anchor="w", padx=5)

numa_frame = tk.Frame(window, bg="#C8E6C9", bd=2, relief="groove")
numa_frame.pack(fill="x", padx=20, pady=5)
numa_title = tk.Label(numa_frame, text="NUMA Nodes", font=("Arial", 12, "bold"), bg="#C8E6C9")
numa_title.pack(anchor="w")
numa_label = scrolledtext.ScrolledText(numa_frame, font=("Arial", 12), bg="#C8E6C9", height=4, wrap="word")
numa_label.pack(fill="x", padx=5)

hyper_frame = tk.Frame(window, bg="#E8F5E9", bd=2, relief="groove")
hyper_frame.pack(fill="x", padx=20, pady=5)
hyper_title = tk.Label(hyper_frame, text="Hyperthreading", font=("Arial", 12, "bold"), bg="#E8F5E9")
hyper_title.pack(anchor="w")
hyper_label = tk.Label(hyper_frame, text="", font=("Arial", 12), bg="#E8F5E9")
hyper_label.pack(anchor="w", padx=5)

physical_frame = tk.Frame(window, bg="#A5D6A7", bd=2, relief="groove")
physical_frame.pack(fill="x", padx=20, pady=5)
physical_title = tk.Label(physical_frame, text="Physical Cores", font=("Arial", 12, "bold"), bg="#A5D6A7")
physical_title.pack(anchor="w")
physical_label = scrolledtext.ScrolledText(physical_frame, font=("Arial", 12), bg="#A5D6A7", height=4, wrap="word")
physical_label.pack(fill="x", padx=5)

sibling_frame = tk.Frame(window, bg="#C8E6C9", bd=2, relief="groove")
sibling_frame.pack(fill="x", padx=20, pady=5)
sibling_title = tk.Label(sibling_frame, text="Sibling Cores", font=("Arial", 12, "bold"), bg="#C8E6C9")
sibling_title.pack(anchor="w")
sibling_label = scrolledtext.ScrolledText(sibling_frame, font=("Arial", 12), bg="#C8E6C9", height=4, wrap="word")
sibling_label.pack(fill="x", padx=5)

# Create a frame to hold the buttons
button_frame = tk.Frame(window)
button_frame.pack(pady=20)  # Adjust pady as needed

# Show CPU Info button
show_button = tk.Button(button_frame, text="Show CPU Info", command=show_cpu_info, font=("Arial", 12), bg="#43A047", fg="white")
show_button.pack(side=tk.LEFT, padx=10)

# Run button to execute the checks
run_button = tk.Button(button_frame, text="Cells to Configure", command=run_checks, font=("Arial", 12), bg="#43A047", fg="white")
run_button.pack(side=tk.LEFT, padx=10)

# Core Alignment button
alignment_button = tk.Button(button_frame, text="Core Alignment", command=do_core_alignment, font=("Arial", 12), bg="#43A047", fg="white")
alignment_button.pack(side=tk.LEFT, padx=10)

# Exit button
exit_button = tk.Button(button_frame, text="Exit", command=window.quit, font=("Arial", 12), bg="#E53935", fg="white")
exit_button.pack(side=tk.LEFT, padx=10)

# Start the Tkinter event loop
window.mainloop()
