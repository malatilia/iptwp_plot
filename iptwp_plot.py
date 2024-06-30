import argparse
import re
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk
from bs4 import BeautifulSoup

parser = argparse.ArgumentParser(description='Plot signal values from IPTWP packets.')
parser.add_argument('file', type=str, help='Path to the PDML export file')

args = parser.parse_args()

signal_values_list = [] # List for all signal values
signals_dict = dict()
timestamps_list = []    # List for the timestamps
t_offset = 0

# Load the PDML file
with open(args.file, 'r') as pdml_file:
    pdml_data = pdml_file.read()

    # Construct a BeautifulSoup object from the PDML data
    soup = BeautifulSoup(pdml_data, 'xml')

    iptwps = soup.find_all('proto', {'name': 'iptwp'})

    # Loop through all packets
    for index, iptwp in enumerate(iptwps):
        tmp = iptwp.find_all('proto')

        # Extract the timestamp of current packet
        process_vars = tmp[0].find_all('field', {'name': 'iptwp.pd.timestamp_in_microsecond'})
        timestamp_str = process_vars[0].get('showname')

        if index == 0:
            t_offset = int(re.search('\d+', timestamp_str).group(0))
        timestamp_value = int(re.search('\d+', timestamp_str).group(0)) - t_offset
        timestamps_list.append(timestamp_value)

        # Loop through all signal names
        process_vars = tmp[0].find_all('field', {'name': 'iptwp.pd.ProcessVariableName'})
        for process_var in process_vars:
            signals = process_var.find_all('field')
            for signal in signals:

                # Extract signal name and value
                signal_str = signal.get('showname')
                signal_name = re.search('\S+', signal_str).group(0)
                signal_value_tmp = re.search('(?<=\[).+?(?=\])+', signal_str).group(0)

                if (signal_value_tmp.find('TRUE') != -1):
                    signal_value = 1
                elif (signal_value_tmp.find('FALSE') != -1):
                    signal_value = 0
                else:
                    signal_value = int(signal_value_tmp)

                # Add signal name and value to a dictionary for the matplotlib
                signal_values_list = []
                if signal_name not in signals_dict:
                    signal_values_list.append(int(signal_value))
                    signals_dict[signal_name] = signal_values_list
                else:
                    signal_values_list = signals_dict[signal_name]
                    signal_values_list.append(int(signal_value))
                    signals_dict[signal_name] = signal_values_list

# Create main window with a treeview to show all selectable signal names
root = tk.Tk()
root.title('IPTWP Plot')
tree = ttk.Treeview(root)
tree.pack(side='left', fill='y')
tree.heading('#0', text='Select Signals')

for item in signals_dict:
    tree.insert('', 'end', text=item)

# Create scrollbar if list too long
scrollbar = tk.Scrollbar(root)
scrollbar.pack(side='right', fill='y')
scrollbar.config(command=tree.yview)

tree.config(yscrollcommand=scrollbar.set)

# Create list to store selected signals
selected_items = []

# Function to select item (click to select, click again to deselect)
def select_item(selected_item):
    item_text = tree.item(selected_item)['text']

    if item_text not in selected_items:
        selected_items.append(item_text)
        tree.item(selected_item, tags="selected")
        tree.tag_configure("selected",foreground="white", background="green")
    else:
        selected_items.remove(item_text)
        tree.item(selected_item, tags="deselected")
        tree.tag_configure("deselected", foreground="black", background="white")

# Function to handle click event
def item_clicked(event):
    item = tree.identify_row(event.y)
    select_item(item)

# Print selected signals
def print_selection():
    plot_i = 1
    for key in signals_dict:

        if key in selected_items:
            # Create plot for each selected signals
            plt.subplot(len(selected_items), 1, plot_i)
            plt.step(timestamps_list, signals_dict[key], where='post')
            plt.ylabel(key)
            plt.xlabel('ms')
            plt.title(key)
            plot_i = plot_i + 1

    plt.tight_layout()
    plt.show()

# Bind treeview click event to function
tree.bind('<Button-1>', item_clicked)

# Create Ok and Cancel buttons
ok_button = tk.Button(root, text='Ok', command=print_selection)
cancel_button = tk.Button(root, text='Cancel', command=root.destroy)

# Display buttons
ok_button.pack(side=tk.BOTTOM, padx=5, pady=5)
cancel_button.pack(side=tk.BOTTOM, padx=5, pady=5)

# Start main loop
root.mainloop()