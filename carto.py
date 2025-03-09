import json
import tkinter as tk
from tkinter import ttk
from tkinter import font
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import mplcursors
import dataParser
import algorithms

# Load airport data
with open("dataset/airline_routes.json", "r") as file:
    airport_data = json.load(file)

# Initialize AirportGraph
airport_graph = dataParser.AirportGraph(airport_data)

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
        
        self.control_font = font.Font(size=12)
        self.create_home_page()
    
    def create_home_page(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.grid_columnconfigure(0, weight=2)
        self.root.grid_columnconfigure(1, weight=8)
        self.root.grid_rowconfigure(0, weight=1)
        
        self.control_frame = tk.Frame(self.root, bg="#f0f0f0")
        self.control_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.control_frame.grid_rowconfigure(0, weight=1)
        
        # Trip type frame
        self.trip_type = tk.StringVar(value="one_way")
        tk.Label(self.control_frame, text="Select Trip Type:", font=self.control_font).pack(anchor='w')
        tk.Radiobutton(self.control_frame, text="One Way", variable=self.trip_type, value="one_way", command=self.toggle_airports, font=self.control_font).pack(anchor='w')
        tk.Radiobutton(self.control_frame, text="Multi-City", variable=self.trip_type, value="multi_city", command=self.toggle_airports, font=self.control_font).pack(anchor='w')
        
        # Departure airport
        self.departure_label = tk.Label(self.control_frame, text="Departure Airport:", font=self.control_font)
        self.departure_label.pack(anchor='w')
        self.departure_airport = ttk.Combobox(self.control_frame, font=self.control_font)
        self.departure_airport.pack(fill=tk.X, padx=5, pady=5)
        self.departure_airport.bind("<KeyRelease>", lambda e: self.hide_route_filter())
        self.departure_airport.bind("<KeyRelease>", lambda e: self.update_dropdown(self.departure_airport), add="+")
        
        # Middle airport (for multi-city trips)
        self.mid_airport_label = tk.Label(self.control_frame, text="Middle Airport:", font=self.control_font)
        self.mid_airport = ttk.Combobox(self.control_frame, state="disabled", font=self.control_font)
        self.mid_airport_label.pack(anchor='w')
        self.mid_airport.pack(fill=tk.X, padx=5, pady=5)
        self.mid_airport.bind("<KeyRelease>", lambda e: self.hide_route_filter())
        self.mid_airport.bind("<KeyRelease>", lambda e: self.update_dropdown(self.mid_airport), add="+")
        
        # Destination airport
        self.destination_label = tk.Label(self.control_frame, text="Destination Airport:", font=self.control_font)
        self.destination_label.pack(anchor='w')
        self.destination_airport = ttk.Combobox(self.control_frame, font=self.control_font)
        self.destination_airport.pack(fill=tk.X, padx=5, pady=5)
        self.destination_airport.bind("<KeyRelease>", lambda e: self.hide_route_filter())
        self.destination_airport.bind("<KeyRelease>", lambda e: self.update_dropdown(self.destination_airport), add="+")
        
        # Search button
        self.search_button = tk.Button(self.control_frame, text="Search", command=self.on_search_clicked, font=self.control_font)
        self.search_button.pack(pady=10)
        
        # Route type filter (initially hidden)
        self.route_type_frame = tk.Frame(self.control_frame)
        self.route_type = tk.StringVar(value="direct")
        tk.Label(self.route_type_frame, text="Filter Routes:", font=self.control_font).pack(anchor='w')
        tk.Radiobutton(self.route_type_frame, text="Direct Routes", variable=self.route_type, value="direct", font=self.control_font).pack(anchor='w')
        tk.Radiobutton(self.route_type_frame, text="Cheapest Routes", variable=self.route_type, value="cheapest", font=self.control_font).pack(anchor='w')
        tk.Radiobutton(self.route_type_frame, text="Shortest Path Routes", variable=self.route_type, value="shortest", font=self.control_font).pack(anchor='w')
        
        # Map frame
        self.map_frame = tk.Frame(self.root)
        self.map_frame.grid(row=0, column=1, sticky="nsew")
        
        # Result list frame below the map
        self.result_frame = tk.Frame(self.root)
        self.result_frame.grid(row=1, column=1, sticky="nsew")
        
        # Scrollable result list
        self.result_canvas = tk.Canvas(self.result_frame, bg="white")
        self.result_scrollbar = ttk.Scrollbar(self.result_frame, orient="vertical", command=self.result_canvas.yview)
        self.result_scrollable_frame = tk.Frame(self.result_canvas)
        
        self.result_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.result_canvas.configure(scrollregion=self.result_canvas.bbox("all")))
        
        self.result_canvas.create_window((0, 0), window=self.result_scrollable_frame, anchor="nw")
        self.result_canvas.configure(yscrollcommand=self.result_scrollbar.set)
        
        self.result_canvas.pack(side="left", fill="both", expand=True)
        self.result_scrollbar.pack(side="right", fill="y")
        
        #call the draw map funct
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
    
    def hide_route_filter(self):
        # Hide route filter options when typing in airport fields
        self.route_type_frame.pack_forget()
    
    def on_search_clicked(self):
        # Show route type filter (aligned with trip type frame)
        self.route_type_frame.pack(pady=0, anchor='w')  # No extra padding, aligned to the left
        
        # Perform search
        self.update_map()
    
    def draw_map(self, plot_airports=False, route=None):
        if hasattr(self, 'canvas'):
            self.canvas.get_tk_widget().destroy()
        
        fig, ax = plt.subplots(figsize=(8, 6), subplot_kw={'projection': ccrs.PlateCarree()})
        ax.set_global()
        
        ax.add_feature(cfeature.OCEAN)
        ax.add_feature(cfeature.LAND)
        ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
        ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5)
        ax.add_feature(cfeature.LAKES, alpha=0.5)
        ax.add_feature(cfeature.RIVERS)
        ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
        
        lons, lats, labels = [], [], []
        for iata, (lat, lon) in valid_airport_coords.items():
            lons.append(lon)
            lats.append(lat)
            labels.append(f"{iata} - {airport_data[iata]['name']}, {airport_data[iata]['country']}")
        
        scatter = ax.scatter(lons, lats, color='#f8f3c1', s=2, transform=ccrs.PlateCarree(), label="Airports") 
        
        cursor = mplcursors.cursor(scatter, hover=True)
        cursor.connect("add", lambda sel: sel.annotation.set_text(labels[sel.index]))
        
        if plot_airports:
            selected_airports = [self.departure_airport.get().split(" - ")[0], self.destination_airport.get().split(" - ")[0]]
            if self.trip_type.get() == "multi_city" and self.mid_airport.get():
                selected_airports.insert(1, self.mid_airport.get().split(" - ")[0])
            
            for airport in selected_airports:
                if airport in valid_airport_coords:
                    lat, lon = valid_airport_coords[airport]
                    ax.scatter(lon, lat, color='red', s=100, transform=ccrs.PlateCarree(), label=airport)
                    ax.text(lon + 2, lat, airport, transform=ccrs.PlateCarree(), fontsize=10, color='black')
        
        if route:
            route_lons = [valid_airport_coords[airport][1] for airport in route]
            route_lats = [valid_airport_coords[airport][0] for airport in route]
            ax.plot(route_lons, route_lats, color='blue', linewidth=2, transform=ccrs.PlateCarree(), label="Route")
        
        self.canvas = FigureCanvasTkAgg(fig, master=self.map_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.draw()
    
    def update_map(self):
        departure = self.departure_airport.get().split(" - ")[0]
        destination = self.destination_airport.get().split(" - ")[0]

        if departure not in valid_airport_coords or destination not in valid_airport_coords:
            return

        route_type = self.route_type.get()

        if self.trip_type.get() == "one_way":
            routes = algorithms.recommend_flights(airport_graph, departure, destination, route_type)
        elif self.trip_type.get() == "multi_city":
            airports = [departure]
            if self.mid_airport.get():
                airports.append(self.mid_airport.get().split(" - ")[0])
            airports.append(destination)
            routes = algorithms.find_multi_city_flights(airport_graph, airports, route_type)

        self.show_results(routes)
    
    def show_results(self, routes):
        for widget in self.result_scrollable_frame.winfo_children():
            widget.destroy()

        if not routes:
            no_results_label = tk.Label(self.result_scrollable_frame, text="No flights found.", font=self.control_font)
            no_results_label.pack(fill=tk.X, padx=5, pady=2)
            return

        for route in routes:
            route_text = " -> ".join([f"{airport} - {airport_data[airport]['name']}, {airport_data[airport]['country']}" for airport in route])
            btn = tk.Button(self.result_scrollable_frame, text=route_text, font=self.control_font, command=lambda r=route: self.draw_map(plot_airports=True, route=r))
            btn.pack(fill=tk.X, padx=5, pady=2)
    
if __name__ == "__main__":
    root = tk.Tk()
    app = MapApp(root)
    root.mainloop()