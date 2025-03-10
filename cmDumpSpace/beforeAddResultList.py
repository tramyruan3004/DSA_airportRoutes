import json
import tkinter as tk
from tkinter import ttk
from tkinter import font  # Import the font module
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import mplcursors  # For hover functionality

# Load airport data
with open("dataset/airline_routes.json", "r") as file:
    airport_data = json.load(file)

# Parse airport coordinates, handling None values
airport_coords = {
    iata: (float(info["latitude"]) if info.get("latitude") is not None else None,
           float(info["longitude"]) if info.get("longitude") is not None else None)
    for iata, info in airport_data.items()
}

# Filter out invalid coordinates
valid_airport_coords = {iata: (lat, lon) for iata, (lat, lon) in airport_coords.items() if lat is not None and lon is not None}

def filter_airports(search_text):
    return [iata for iata, info in airport_data.items() if search_text in iata or search_text in info.get("name", "").upper()]

class MapApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Flight Search Map")
        
        # Define a larger font for the control frame
        self.control_font = font.Font(size=12)  # Adjust the size as needed
        
        self.create_home_page()
    
    def create_home_page(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Use grid geometry manager for resizable layout
        self.root.grid_columnconfigure(0, weight=2)  # Control frame takes 20% of width
        self.root.grid_columnconfigure(1, weight=8)  # Map frame takes 80% of width
        self.root.grid_rowconfigure(0, weight=1)     # Single row takes full height
        
        # Control frame on the left side (20% width)
        self.control_frame = tk.Frame(self.root, bg="#f0f0f0")
        self.control_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Configure control frame to expand vertically
        self.control_frame.grid_rowconfigure(0, weight=1)
        
        # Apply the custom font to all widgets in the control frame
        self.trip_type = tk.StringVar(value="one_way")
        tk.Label(self.control_frame, text="Select Trip Type:", font=self.control_font).pack(anchor='w')
        tk.Radiobutton(self.control_frame, text="One Way", variable=self.trip_type, value="one_way", command=self.toggle_airports, font=self.control_font).pack(anchor='w')
        tk.Radiobutton(self.control_frame, text="Multi-City", variable=self.trip_type, value="multi_city", command=self.toggle_airports, font=self.control_font).pack(anchor='w')
        
        self.departure_label = tk.Label(self.control_frame, text="Departure Airport:", font=self.control_font)
        self.departure_label.pack(anchor='w')
        self.departure_airport = ttk.Combobox(self.control_frame, font=self.control_font)
        self.departure_airport.pack(fill=tk.X, padx=5, pady=5)
        self.departure_airport.bind("<KeyRelease>", lambda e: self.update_dropdown(self.departure_airport))
        
        self.mid_airport_label = tk.Label(self.control_frame, text="Middle Airport:", font=self.control_font)
        self.mid_airport = ttk.Combobox(self.control_frame, state="disabled", font=self.control_font)
        self.mid_airport_label.pack(anchor='w')
        self.mid_airport.pack(fill=tk.X, padx=5, pady=5)
        self.mid_airport.bind("<KeyRelease>", lambda e: self.update_dropdown(self.mid_airport))
        
        self.destination_label = tk.Label(self.control_frame, text="Destination Airport:", font=self.control_font)
        self.destination_label.pack(anchor='w')
        self.destination_airport = ttk.Combobox(self.control_frame, font=self.control_font)
        self.destination_airport.pack(fill=tk.X, padx=5, pady=5)
        self.destination_airport.bind("<KeyRelease>", lambda e: self.update_dropdown(self.destination_airport))
        
        self.search_button = tk.Button(self.control_frame, text="Search", command=self.update_map, font=self.control_font)
        self.search_button.pack(pady=10)
        
        # Map frame on the right side (80% width)
        self.map_frame = tk.Frame(self.root)
        self.map_frame.grid(row=0, column=1, sticky="nsew")
        
        self.draw_map()
    
    def toggle_airports(self):
        if self.trip_type.get() == "multi_city":
            self.mid_airport["state"] = "normal"
        else:
            self.mid_airport["state"] = "disabled"
    
    def update_dropdown(self, combobox):
        search_text = combobox.get().upper()
        if search_text:
            filtered_airports = [f"{iata} - {airport_data[iata]['name']}" for iata in valid_airport_coords if search_text in iata or search_text in airport_data[iata].get("name", "").upper()]
            combobox["values"] = filtered_airports
        else:
            combobox["values"] = [f"{iata} - {airport_data[iata]['name']}" for iata in valid_airport_coords]
    
    def draw_map(self, plot_airports=False):
        if hasattr(self, 'canvas'):
            self.canvas.get_tk_widget().destroy()
        
        fig, ax = plt.subplots(figsize=(8, 6), subplot_kw={'projection': ccrs.PlateCarree()})
        ax.set_global()
        
        # Add map features
        ax.add_feature(cfeature.OCEAN)
        ax.add_feature(cfeature.LAND)
        ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
        ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5)
        ax.add_feature(cfeature.LAKES, alpha=0.5)
        ax.add_feature(cfeature.RIVERS)
        ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
        
        # Plot all valid airports
        lons, lats, labels = [], [], []
        for iata, (lat, lon) in valid_airport_coords.items():
            lons.append(lon)
            lats.append(lat)
            labels.append(f"{iata} - {airport_data[iata]['name']}, {airport_data[iata]['country']}")
        
        scatter = ax.scatter(lons, lats, color='#f8f3c1', s=2, transform=ccrs.PlateCarree(), label="Airports") 
        
        # Add hover functionality
        cursor = mplcursors.cursor(scatter, hover=True)
        cursor.connect("add", lambda sel: sel.annotation.set_text(labels[sel.index]))
        
        # Plot selected airports (if any)
        if plot_airports:
            selected_airports = [self.departure_airport.get().split(" - ")[0], self.destination_airport.get().split(" - ")[0]]
            if self.trip_type.get() == "multi_city" and self.mid_airport.get():
                selected_airports.insert(1, self.mid_airport.get().split(" - ")[0])
            
            for airport in selected_airports:
                if airport in valid_airport_coords:
                    lat, lon = valid_airport_coords[airport]
                    ax.scatter(lon, lat, color='red', s=100, transform=ccrs.PlateCarree(), label=airport)
                    ax.text(lon + 2, lat, airport, transform=ccrs.PlateCarree(), fontsize=10, color='black')
        
        self.canvas = FigureCanvasTkAgg(fig, master=self.map_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.draw()
    
    def update_map(self):
        self.draw_map(plot_airports=True)
    
if __name__ == "__main__":
    root = tk.Tk()
    app = MapApp(root)
    root.mainloop()