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

# Parse airport coordinates
airport_coords = {
    iata: (float(info["latitude"]) if info.get("latitude") else None,
           float(info["longitude"]) if info.get("longitude") else None)
    for iata, info in airport_data.items()
}

# Filter out invalid coords
valid_airport_coords = {
    iata: (lat, lon)
    for iata, (lat, lon) in airport_coords.items()
    if lat is not None and lon is not None
}

class MapApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Flight Search Map")

        self.control_font = font.Font(size=12)
        self.create_home_page()

    def create_home_page(self):
        # Clear existing UI
        for widget in self.root.winfo_children():
            widget.destroy()

        # Configure grid layout
        self.root.grid_columnconfigure(0, weight=2)
        self.root.grid_columnconfigure(1, weight=8)
        self.root.grid_rowconfigure(0, weight=1)

        # Left control panel
        self.control_frame = tk.Frame(self.root, bg="#f0f0f0")
        self.control_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.control_frame.grid_rowconfigure(0, weight=1)

        #
        # -------------- TRIP TYPE --------------
        #
        self.trip_type_var = tk.StringVar(value="one_way")
        tk.Label(self.control_frame, text="Trip Type:", font=self.control_font).pack(anchor='w', pady=5)

        tk.Radiobutton(
            self.control_frame, text="One Way", variable=self.trip_type_var,
            value="one_way", command=self.toggle_middle_airport,
            font=self.control_font
        ).pack(anchor='w')

        tk.Radiobutton(
            self.control_frame, text="Multi-City", variable=self.trip_type_var,
            value="multi_city", command=self.toggle_middle_airport,
            font=self.control_font
        ).pack(anchor='w')

        #
        # -------------- DEPARTURE AIRPORT --------------
        #
        tk.Label(self.control_frame, text="Departure Airport:", font=self.control_font).pack(anchor='w')
        self.departure_airport = ttk.Combobox(self.control_frame, font=self.control_font)
        self.departure_airport.pack(fill=tk.X, padx=5, pady=5)
        self.departure_airport.bind("<KeyRelease>", lambda e: self.update_dropdown(self.departure_airport))

        #
        # -------------- MIDDLE AIRPORT --------------
        #
        tk.Label(self.control_frame, text="Middle Airport:", font=self.control_font).pack(anchor='w')
        self.mid_airport = ttk.Combobox(self.control_frame, font=self.control_font, state="disabled")
        self.mid_airport.pack(fill=tk.X, padx=5, pady=5)
        self.mid_airport.bind("<KeyRelease>", lambda e: self.update_dropdown(self.mid_airport))

        #
        # -------------- DESTINATION AIRPORT --------------
        #
        tk.Label(self.control_frame, text="Destination Airport:", font=self.control_font).pack(anchor='w')
        self.destination_airport = ttk.Combobox(self.control_frame, font=self.control_font)
        self.destination_airport.pack(fill=tk.X, padx=5, pady=5)
        self.destination_airport.bind("<KeyRelease>", lambda e: self.update_dropdown(self.destination_airport))

        # Pre-fill with all valid airports
        full_list = [
            f"{iata} - {airport_data[iata]['name']}"
            for iata in valid_airport_coords
        ]
        self.departure_airport["values"] = full_list
        self.mid_airport["values"] = full_list
        self.destination_airport["values"] = full_list

        #
        # -------------- ROUTE TYPE --------------
        #
        self.route_type_frame = tk.LabelFrame(self.control_frame, text="Route Type", font=self.control_font, padx=5, pady=5)
        self.route_type_frame.pack(fill=tk.X, padx=5, pady=5)

        self.route_type_var = tk.StringVar(value="direct")
        tk.Radiobutton(self.route_type_frame, text="Direct (0 stops)", variable=self.route_type_var,
                       value="direct", font=self.control_font).pack(anchor='w')
        tk.Radiobutton(self.route_type_frame, text="1-stop flight", variable=self.route_type_var,
                       value="one_stop", font=self.control_font).pack(anchor='w')
        tk.Radiobutton(self.route_type_frame, text="2-stop flight", variable=self.route_type_var,
                       value="two_stop", font=self.control_font).pack(anchor='w')

        #
        # -------------- FILTER (Cheapest / Fastest) --------------
        #
        self.filter_frame = tk.LabelFrame(self.control_frame, text="Filter", font=self.control_font, padx=5, pady=5)
        self.filter_frame.pack(fill=tk.X, padx=5, pady=5)

        self.filter_var = tk.StringVar(value="cheapest")
        tk.Radiobutton(self.filter_frame, text="Cheapest Route", variable=self.filter_var,
                       value="cheapest", font=self.control_font).pack(anchor='w')
        tk.Radiobutton(self.filter_frame, text="Fastest Route", variable=self.filter_var,
                       value="fastest", font=self.control_font).pack(anchor='w')

        #
        # -------------- CABIN --------------
        #
        self.cabin_frame = tk.LabelFrame(self.control_frame, text="Cabin", font=self.control_font, padx=5, pady=5)
        self.cabin_frame.pack(fill=tk.X, padx=5, pady=5)

        self.cabin_var = tk.StringVar(value="Economy")
        tk.Radiobutton(self.cabin_frame, text="Economy", variable=self.cabin_var, value="Economy", font=self.control_font).pack(anchor='w')
        tk.Radiobutton(self.cabin_frame, text="Premium Economy", variable=self.cabin_var, value="Premium Economy", font=self.control_font).pack(anchor='w')
        tk.Radiobutton(self.cabin_frame, text="Business", variable=self.cabin_var, value="Business", font=self.control_font).pack(anchor='w')
        tk.Radiobutton(self.cabin_frame, text="First", variable=self.cabin_var, value="First", font=self.control_font).pack(anchor='w')

        #
        # -------------- SEARCH BUTTON --------------
        #
        self.search_button = tk.Button(
            self.control_frame, text="Search", command=self.on_search_clicked, font=self.control_font
        )
        self.search_button.pack(pady=10)  # Clearly visible at the bottom

        # Right side: map and results
        self.map_frame = tk.Frame(self.root)
        self.map_frame.grid(row=0, column=1, sticky="nsew")

        self.result_frame = tk.Frame(self.root)
        self.result_frame.grid(row=1, column=1, sticky="nsew")

        # Scrollable result
        self.result_canvas = tk.Canvas(self.result_frame, bg="white")
        self.result_scrollbar = ttk.Scrollbar(self.result_frame, orient="vertical", command=self.result_canvas.yview)
        self.result_scrollable_frame = tk.Frame(self.result_canvas)

        self.result_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.result_canvas.configure(scrollregion=self.result_canvas.bbox("all"))
        )

        self.result_canvas.create_window((0, 0), window=self.result_scrollable_frame, anchor="nw")
        self.result_canvas.configure(yscrollcommand=self.result_scrollbar.set)

        self.result_canvas.pack(side="left", fill="both", expand=True)
        self.result_scrollbar.pack(side="right", fill="y")

        self.draw_map()

    def toggle_middle_airport(self):
        """
        If user selects 'one_way', disable the middle airport combobox.
        If user selects 'multi_city', enable it.
        """
        if self.trip_type_var.get() == "multi_city":
            self.mid_airport["state"] = "normal"
        else:
            self.mid_airport["state"] = "disabled"

    def update_dropdown(self, combobox):
        typed_text = combobox.get().strip().upper()

        full_list = [
            f"{iata} - {airport_data[iata]['name']}"
            for iata in valid_airport_coords
        ]

        if typed_text:
            filtered = [
                item for item in full_list
                if typed_text in item.upper()
            ]
        else:
            filtered = full_list

        combobox["values"] = filtered

    def on_search_clicked(self):
        # The method that triggers the BFS / multi-city logic
        self.update_map()

    def draw_map(self, route=None):
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

        # Plot all airports
        lons, lats, labels = [], [], []
        for iata, (lat, lon) in valid_airport_coords.items():
            lons.append(lon)
            lats.append(lat)
            labels.append(f"{iata} - {airport_data[iata]['name']}, {airport_data[iata]['country']}")

        scatter = ax.scatter(lons, lats, color='#f8f3c1', s=2, transform=ccrs.PlateCarree(), label="Airports")
        cursor = mplcursors.cursor(scatter, hover=True)
        cursor.connect("add", lambda sel: sel.annotation.set_text(labels[sel.index]))

        # If a route is provided, highlight it
        if route:
            route_lons = []
            route_lats = []
            for airport in route:
                if airport in valid_airport_coords:
                    lat, lon = valid_airport_coords[airport]
                    route_lons.append(lon)
                    route_lats.append(lat)
                    ax.scatter(lon, lat, color='red', s=100, transform=ccrs.PlateCarree())
                    ax.text(lon + 2, lat, airport, transform=ccrs.PlateCarree(), fontsize=10, color='black')

            ax.plot(route_lons, route_lats, color='blue', linewidth=2, transform=ccrs.PlateCarree())

        self.canvas = FigureCanvasTkAgg(fig, master=self.map_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.draw()

    def update_map(self):
        # Clear old results from the result scrollable frame
        for widget in self.result_scrollable_frame.winfo_children():
            widget.destroy()

        # Retrieve user selections
        trip_type = self.trip_type_var.get()  # "one_way" or "multi_city"
        dep_raw = self.departure_airport.get().split(" - ")
        mid_raw = self.mid_airport.get().split(" - ")
        dest_raw = self.destination_airport.get().split(" - ")

        if len(dep_raw) < 2:
            self.show_message("Invalid Departure Airport.")
            self.draw_map()
            return
        if len(dest_raw) < 2:
            self.show_message("Invalid Destination Airport.")
            self.draw_map()
            return

        departure = dep_raw[0]
        destination = dest_raw[0]

        # Route type => direct=0, one_stop=1, two_stop=2
        route_type = self.route_type_var.get()
        if route_type == "direct":
            stops = 0
        elif route_type == "one_stop":
            stops = 1
        else:
            stops = 2

        # Filter => cheapest or fastest
        filter_choice = self.filter_var.get()

        # Cabin => economy/premium/business/first
        cabin_choice = self.cabin_var.get()

        # If one_way => BFS from departure->destination
        if trip_type == "one_way":
            # Example BFS call
            routes = algorithms.find_one_way_flights(
                graph=airport_graph,
                departure=departure,
                destination=destination,
                stops=stops,
                filter_type=filter_choice,
                cabin=cabin_choice
            )
            self.display_routes(routes)
        else:
            # multi_city => departure->middle->destination
            if len(mid_raw) < 2:
                self.show_message("Invalid Middle Airport.")
                self.draw_map()
                return
            middle = mid_raw[0]

            # BFS for departure->middle
            routes_dep_mid = algorithms.find_one_way_flights(
                graph=airport_graph,
                departure=departure,
                destination=middle,
                stops=stops,
                filter_type=filter_choice,
                cabin=cabin_choice
            )
            # BFS for middle->destination
            routes_mid_dest = algorithms.find_one_way_flights(
                graph=airport_graph,
                departure=middle,
                destination=destination,
                stops=stops,
                filter_type=filter_choice,
                cabin=cabin_choice
            )

            # Merge routes (simple approach)
            merged_routes = []
            for (r1, dist1, time1, cost1, c1) in routes_dep_mid:
                for (r2, dist2, time2, cost2, c2) in routes_mid_dest:
                    combined_path = r1[:-1] + r2  # remove the duplicate 'middle'
                    total_dist = dist1 + dist2
                    total_time = time1 + time2
                    total_cost = cost1 + cost2
                    merged_routes.append((combined_path, total_dist, total_time, total_cost, cabin_choice))

            # Sort by cost or time
            if filter_choice == "cheapest":
                merged_routes.sort(key=lambda x: x[3])
            else:
                merged_routes.sort(key=lambda x: x[2])

            self.display_routes(merged_routes)

    def show_message(self, msg):
        tk.Label(self.result_scrollable_frame, text=msg, font=self.control_font).pack(fill=tk.X, padx=5, pady=2)

    def display_routes(self, routes):
        if not routes:
            self.show_message("No flights found.")
            self.draw_map()
            return

        # Show the first route on the map
        first_route = routes[0][0]
        self.draw_map(route=first_route)

        # Display each route
        for (routelist, dist, timing, cost, cabin) in routes:
            # Build multiline text
            segments = []
            for airport in routelist:
                airport_name = airport_data[airport]["name"]
                segments.append(f"{airport} ({airport_name})")
            route_line = " -> ".join(segments)

            display_str = (
                f"{route_line}\n"
                f"  Total Distance: {dist} km\n"
                f"  Total Timing: {timing} min\n"
                f"  Price: ${cost:.2f} ({cabin})"
            )

            btn = tk.Button(
                self.result_scrollable_frame,
                text=display_str,
                font=self.control_font,
                justify="left",
                anchor="w",
                wraplength=500,
                command=lambda r=routelist: self.draw_map(route=r)
            )
            btn.pack(fill=tk.X, padx=5, pady=5)

if __name__ == "__main__":
    root = tk.Tk()
    app = MapApp(root)
    root.mainloop()
