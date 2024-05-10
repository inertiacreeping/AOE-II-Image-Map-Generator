import os
import logging
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageFilter
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from AoE2ScenarioParser.objects.managers.map_manager import MapManager
from AoE2ScenarioParser.scenarios.aoe2_de_scenario import AoE2DEScenario

# Declare global variables
img_path = ""
processed_image = None
quantized_array = None
color_count_slider = None
simplification_slider = None
centers = None
terrains = pd.read_csv('Terrains.csv')
color_to_dropdown = {}
dropdown_frames = []
input_folder = os.path.dirname(os.path.abspath(__file__))
scenario = AoE2DEScenario.from_file(os.path.join(input_folder, "hello world.aoe2scenario"))

# Setup logging configuration
logging.basicConfig(filename='MapGeneratorLog.log', level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger('MapGeneratorLog')

def setup_logging():
    # Create logger
    logger = logging.getLogger('MapGeneratorLog')
    logger.setLevel(logging.DEBUG)

    # Create file handler which logs even debug messages
    fh = logging.FileHandler('map_generation.log')
    fh.setLevel(logging.DEBUG)

    # Create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(fh)
    return logger

def create_or_update_scenario():
    global scenario, size_var
    map_size = int(size_var.get())  # Assuming size_var holds the desired map size
    scenario.map.width = map_size
    scenario.map.height = map_size

    # Add other scenario modifications here

    # To save the scenario to a file after modifications
    scenario.write_to_file(os.path.join(input_folder, "modified_hello_world.aoe2scenario"))

def open_image():
    global img_path, processed_image, quantized_array
    img_path = filedialog.askopenfilename()
    if img_path:
        process_button.config(state=tk.NORMAL)
        processed_image = None
        quantized_array = None
        update_canvas()

def generate_bitmap():
    global processed_image, centers, quantized_array, color_count_slider, simplification_slider
    number_of_colors = color_count_slider.get()
    simplification_level = simplification_slider.get()  # Get the simplification level from the slider
    size = size_var.get() 
    original_image = Image.open(img_path).convert('RGB')

    # Ensure the image is square first
    max_dim = max(original_image.size)
    original_image = original_image.resize((max_dim, max_dim), Image.Resampling.LANCZOS)

    # Apply Gaussian blur based on the simplification level
    if simplification_level > 0:
        original_image = original_image.filter(ImageFilter.GaussianBlur(radius=simplification_level))

    # Rotate and then resize to the selected map size
    processing_image = original_image.rotate(0, expand=True) # -45 to rotate if required
    map_image = processing_image.resize((size, size), Image.Resampling.LANCZOS)

    np_image = np.array(map_image).reshape(-1, 3)
    kmeans = KMeans(n_clusters=number_of_colors, random_state=0).fit(np_image)
    labels = kmeans.labels_
    centers = np.uint8(kmeans.cluster_centers_)
    quantized_image = centers[labels].reshape(map_image.size[1], map_image.size[0], 3)

    # Resize the quantized image back to a fixed display size for consistent visualization
    display_size = 500  # Adjust based on your canvas size
    display_image = Image.fromarray(quantized_image, 'RGB').resize((display_size, display_size), Image.Resampling.NEAREST)

    processed_image = display_image
    quantized_array = np.array(display_image)

    update_canvas()
    update_color_swatches(centers)

def init_ui():
    global color_count_slider, simplification_slider, root, canvas, process_button, size_var, map_sizes, color_swatches_frame

    root = tk.Tk()
    root.title("Age of Empires II Map Generator")

    control_frame = tk.Frame(root, width=350)  # Adjust the width as needed
    control_frame.pack(side='left', fill='y', padx=10, pady=10)

    color_swatches_frame = tk.Frame(root)
    color_swatches_frame.pack(side='right', fill='both', expand=True, padx=10, pady=10)

    color_count_slider = tk.Scale(control_frame, from_=1, to=20, orient='horizontal', label='Number of Colors', length=200)
    color_count_slider.set(2)
    color_count_slider.pack()

    simplification_slider = tk.Scale(control_frame, from_=0, to=50, orient='horizontal', label='Simplification Level', length=200)
    simplification_slider.set(0)
    simplification_slider.pack()

    open_button = tk.Button(control_frame, text="Open Image", command=open_image)
    open_button.pack()

    map_sizes = { "Tiny (120)": 120, "Small (144)": 144, "Medium (168)": 168, "Normal (200)": 200, "Large (220)": 220, "Giant (240)": 240, "Ludikrous (480)": 480 }
    size_var = tk.IntVar(value=480)  # Default to the numeric part of 'Ludicrous (480)'
    
    for label, size in map_sizes.items():
        rb = tk.Radiobutton(control_frame, text=label, variable=size_var, value=size)
        rb.pack()

    process_button = tk.Button(control_frame, text="Generate Bitmap", state=tk.DISABLED, command=generate_bitmap)
    process_button.pack()

    canvas = tk.Canvas(control_frame, width=550, height=550)
    canvas.pack()
    export_button = tk.Button(control_frame, text="Export aoe2scenario Map", command=export_rms)
    export_button.pack()

    root.mainloop()

# Initialize scenario
def initialize_scenario():
    global scenario
    scenario = AoE2DEScenario.from_file(os.path.join(input_folder, "hello world.aoe2scenario"))

def export_rms():
    global scenario, quantized_array, color_to_dropdown, terrains

    # Make sure scenario is initialized
    if not scenario:
        initialize_scenario()

    # Access the map manager from the scenario
    map_manager = scenario.map_manager

    # Update map size dynamically based on user input
    map_size = int(size_var.get())
    map_manager.map_size = map_size

    logger.debug("Map size set to: {}".format(map_size))

    # Iterate over each pixel in the quantized array, ensuring indices are within bounds
    for y in range(min(quantized_array.shape[0], map_manager.map_size)):
        for x in range(min(quantized_array.shape[1], map_manager.map_size)):
            color = tuple(quantized_array[y, x])
            if color in color_to_dropdown:
                terrain_type = color_to_dropdown[color].get()  # Get the terrain type from dropdown
                terrain_id = int(terrains[terrains['Descriptive_Name'] == terrain_type]['Constant_ID'].values[0])
                tile = map_manager.get_tile(x, y)
                tile.terrain_id = terrain_id
                logger.info("Setting tile at ({}, {}) to color {} with terrain ID {}".format(x, y, color, terrain_id))
            else:
                logger.warning("No terrain defined for color: {}".format(color))

    # Save the scenario with terrain modifications
    scenario.write_to_file(os.path.join(input_folder, "modified_hello_world.aoe2scenario"))
    logger.info("The map has been exported successfully to {}".format(os.path.join(input_folder, "modified_hello_world.aoe2scenario")))

def update_canvas():
    global canvas_image
    if processed_image is not None:
        tk_image = ImageTk.PhotoImage(processed_image)
        canvas.create_image(20, 20, anchor=tk.NW, image=tk_image)
        canvas.image = tk_image

        north_label = tk.Label(canvas, text="NORTH", font=('Arial', 8, 'bold'))
        north_label.place(x=17, y=0)
        east_label = tk.Label(canvas, text="EAST", font=('Arial', 8, 'bold'))
        east_label.place(x=canvas.winfo_width() - 65, y=0)
        south_label = tk.Label(canvas, text="SOUTH", font=('Arial', 8, 'bold'))
        south_label.place(x=17, y=canvas.winfo_height() - 33)
        west_label = tk.Label(canvas, text="WEST", font=('Arial', 8, 'bold'))
        west_label.place(x=canvas.winfo_width() - 65, y=canvas.winfo_height() - 33)
    else:
        canvas.delete("all")

def update_color_swatches(centers):
    # Clear existing swatches
    for widget in color_swatches_frame.winfo_children():
        widget.destroy()

    for color in centers:
        frame = tk.Frame(color_swatches_frame, borderwidth=1, relief="raised")
        frame.pack(side="top", fill="x", padx=5, pady=5)

        color_label = tk.Label(frame, background='#%02x%02x%02x' % tuple(color), width=10, height=2)
        color_label.pack(side="left", padx=10)

        dropdown_var = tk.StringVar(frame)
        dropdown_var.set("Select Terrain")
        dropdown = ttk.Combobox(frame, textvariable=dropdown_var, values=terrains['Descriptive_Name'].tolist())
        dropdown.pack(side="right", padx=10)

        color_to_dropdown[tuple(color)] = dropdown_var  # Store the StringVar, not the frame

        flash_button = tk.Button(frame, text="Flash", command=lambda c=color: flash_color(c))
        flash_button.pack(side="right", padx=10)

def flash_color(color):
    global quantized_array
    if quantized_array is not None:
        original_colors = np.copy(quantized_array)  # Make a copy of the original for resetting later
        mask = np.all(quantized_array == color, axis=-1)
        if np.any(mask):
            quantized_array[mask] = [255, 255, 255]  # Change to white
            display_image = Image.fromarray(quantized_array, 'RGB').resize((500, 500), Image.Resampling.NEAREST)
            tk_image = ImageTk.PhotoImage(display_image)
            canvas.create_image(20, 20, anchor=tk.NW, image=tk_image)
            canvas.image = tk_image
            root.after(500, lambda: reset_flash(original_colors))  # Ensure correct function call
        else:
            messagebox.showinfo("Error", "No pixels found with the selected color to flash.")
    else:
        messagebox.showinfo("Error", "Image not processed or available for flashing.")

def reset_flash(original_colors):
    global quantized_array
    quantized_array = original_colors  # Reset the quantized_array with the original colors
    display_image = Image.fromarray(quantized_array, 'RGB').resize((500, 500), Image.Resampling.NEAREST)
    tk_image = ImageTk.PhotoImage(display_image)
    canvas.create_image(20, 20, anchor=tk.NW, image=tk_image)
    canvas.image = tk_image

if __name__ == "__main__":
    init_ui()
