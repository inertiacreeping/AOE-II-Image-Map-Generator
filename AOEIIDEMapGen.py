import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageFilter
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans

# Declare global variables
img_path = ""
processed_image = None
quantized_array = None
centers = None
terrains = pd.read_csv('Terrains.csv')
color_to_dropdown = {}
dropdown_frames = []

# Global variables for UI elements
color_count_slider = None
simplification_slider = None

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
    size = map_sizes[size_var.get()]
    original_image = Image.open(img_path).convert('RGB')

    # Ensure the image is square first
    max_dim = max(original_image.size)
    original_image = original_image.resize((max_dim, max_dim), Image.Resampling.LANCZOS)

    # Apply Gaussian blur based on the simplification level
    if simplification_level > 0:
        original_image = original_image.filter(ImageFilter.GaussianBlur(radius=simplification_level))

    # Rotate and then resize to the selected map size
    processing_image = original_image.rotate(-45, expand=True)
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
    color_count_slider.set(8)
    color_count_slider.pack()

    simplification_slider = tk.Scale(control_frame, from_=0, to=50, orient='horizontal', label='Simplification Level', length=200)
    simplification_slider.set(0)
    simplification_slider.pack()

    open_button = tk.Button(control_frame, text="Open Image", command=open_image)
    open_button.pack()

    map_sizes = { "Tiny": 120, "Small": 144, "Medium": 168, "Normal": 200, "Large": 220, "Giant": 240, "Ludicrous": 480 }
    size_var = tk.StringVar(value="Ludicrous")

    for size, dimension in map_sizes.items():
        rb = tk.Radiobutton(control_frame, text=size, variable=size_var, value=size)
        rb.pack()

    process_button = tk.Button(control_frame, text="Generate Bitmap", state=tk.DISABLED, command=generate_bitmap)
    process_button.pack()

    canvas = tk.Canvas(control_frame, width=550, height=550)
    canvas.pack()
    export_button = tk.Button(control_frame, text="Export RMS Map", command=export_rms)
    export_button.pack()

    root.mainloop()

def export_rms():
    # Prepare the RMS content header
    rms_content = "/* Random Map Script */\n"
    rms_content += "/* Automatically generated */\n\n"
    rms_content += "create_land {\n"
    rms_content += "    base_terrain GRASS\n"  # Default terrain, change as needed
    rms_content += "    land_percent 100\n"
    rms_content += "    terrain_type GRASS\n"
    rms_content += "    other_zone_avoidance_distance 0\n"
    rms_content += "}\n\n"

    # This example assumes a simple approach to demonstrate the concept
    # In practice, you would generate the map with more specific commands for each tile based on your game's scripting capabilities
    for y in range(quantized_array.shape[0]):
        for x in range(quantized_array.shape[1]):
            color = tuple(quantized_array[y, x][:3])  # Get RGB color
            terrain_type = color_to_dropdown[color][0].get() if color in color_to_dropdown else "GRASS"
            # You might need to convert terrain_type to an actual command or ID used in RMS scripts
            # Here we simply note it as a comment for each coordinate for demonstration
            rms_content += f"/* Terrain at ({x}, {y}): {terrain_type} */\n"

    # Save RMS file
    with open("custom_map.rms", "w") as file:
        file.write(rms_content)

    print("RMS file has been created.")

def update_canvas():
    global canvas_image
    if processed_image is not None:
        tk_image = ImageTk.PhotoImage(processed_image)
        canvas.create_image(20, 20, anchor=tk.NW, image=tk_image)
        canvas.image = tk_image
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

        flash_button = tk.Button(frame, text="Flash", command=lambda c=color: flash_color(c))
        flash_button.pack(side="right", padx=10)

        color_to_dropdown[tuple(color)] = (dropdown_var, frame)

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