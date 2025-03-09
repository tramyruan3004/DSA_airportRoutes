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

# Load currency data (with "name" field, but "symbol" = currency code)
with open("dataset/currency.json", "r") as cf:
    currency_data = json.load(cf)

currency_rates = currency_data["rates"]  # e.g. { "SGD": {"symbol":"SGD","rate":1.0,"name":"Singapore Dollar"}, ... }

class MapApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Flight Search Map")

        # Use a Unicode-friendly font if you wish, e.g. "Noto Sans"
        # But since we are using codes like "USD", "SGD", we can pick any common font
        self.control_font = font.Font(family="Noto Sans", size=12)
        self.create_home_page()

    def create_home_page(self):
        # Clear existing UI
        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.grid_columnconfigure(0, weight=2)
        self.root.grid_columnconfigure(1, weight=8)
        self.root.grid_rowconfigure(0, weight=1)

        # Left control panel
        self.control_frame = tk.Frame(self.root, bg="#f0f0f0")
        self.control_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.control_frame.grid_rowconfigure(0, weight=1)

        #
        # ===== CURRENCY COMBOBOX =====
        #
        tk.Label(self.control_frame, text="Currency:", font=self.control_font).pack(anchor='w', pady=5)
        self.currency_var = tk.StringVar()

        # Build a list like ["SGD - Singapore Dollar", "USD - United States Dollar", ...]
        currency_list = [
            f"{code} - {info['name']}"
            for code, info in currency_rates.items()
        ]
        self.currency_combo = ttk.Combobox(self.control_frame, textvariable=self.currency_var,
                                           values=currency_list, font=self.control_font)
        self.currency_combo.pack(fill=tk.X, padx=5, pady=5)
        # default to "SGD - Singapore Dollar"
        self.currency_var.set("SGD - Singapore Dollar")

        #
        # ===== TRIP TYPE (ONE WAY / MULTI-CITY) =====
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

        # DEPARTURE
        tk.Label(self.control_frame, text="Departure Airport:", font=self.control_font).pack(anchor='w')
        self.departure_airport = ttk.Combobox(self.control_frame, font=self.control_font)
        self.departure_airport.pack(fill=tk.X, padx=5, pady=5)

        # dynamic filtering
        self.departure_airport.bind("<KeyRelease>", lambda e: self.update_dropdown(self.departure_airport))

        # MIDDLE
        tk.Label(self.control_frame, text="Middle Airport:", font=self.control_font).pack(anchor='w')
        self.mid_airport = ttk.Combobox(self.control_frame, font=self.control_font, state="disabled")
        self.mid_airport.pack(fill=tk.X, padx=5, pady=5)
        self.mid_airport.bind("<KeyRelease>", lambda e: self.update_dropdown(self.mid_airport))

        # DESTINATION
        tk.Label(self.control_frame, text="Destination Airport:", font=self.control_font).pack(anchor='w')
        self.destination_airport = ttk.Combobox(self.control_frame, font=self.control_font)
        self.destination_airport.pack(fill=tk.X, padx=5, pady=5)
        self.destination_airport.bind("<KeyRelease>", lambda e: self.update_dropdown(self.destination_airport))

        # Pre-fill combobox with valid airports
        full_list = [
            f"{iata} - {airport_data[iata]['name']}"
            for iata in valid_airport_coords
        ]
        self.departure_airport["values"] = full_list
        self.mid_airport["values"] = full_list
        self.destination_airport["values"] = full_list

        #
        # ===== ROUTE TYPE (direct, 1-stop, 2-stop) =====
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
        # ===== FILTER (Cheapest / Fastest) =====
        #
        self.filter_frame = tk.LabelFrame(self.control_frame, text="Filter", font=self.control_font, padx=5, pady=5)
        self.filter_frame.pack(fill=tk.X, padx=5, pady=5)
        self.filter_var = tk.StringVar(value="cheapest")
        tk.Radiobutton(self.filter_frame, text="Cheapest Route", variable=self.filter_var,
                       value="cheapest", font=self.control_font).pack(anchor='w')
        tk.Radiobutton(self.filter_frame, text="Fastest Route", variable=self.filter_var,
                       value="fastest", font=self.control_font).pack(anchor='w')

        #
        # ===== CABIN =====
        #
        self.cabin_frame = tk.LabelFrame(self.control_frame, text="Cabin", font=self.control_font, padx=5, pady=5)
        self.cabin_frame.pack(fill=tk.X, padx=5, pady=5)
        self.cabin_var = tk.StringVar(value="Economy")
        tk.Radiobutton(self.cabin_frame, text="Economy", variable=self.cabin_var, value="Economy", font=self.control_font).pack(anchor='w')
        tk.Radiobutton(self.cabin_frame, text="Premium Economy", variable=self.cabin_var, value="Premium Economy", font=self.control_font).pack(anchor='w')
        tk.Radiobutton(self.cabin_frame, text="Business", variable=self.cabin_var, value="Business", font=self.control_font).pack(anchor='w')
        tk.Radiobutton(self.cabin_frame, text="First", variable=self.cabin_var, value="First", font=self.control_font).pack(anchor='w')

        #
        # ===== SEARCH BUTTON =====
        #
        self.search_button = tk.Button(
            self.control_frame, text="Search", command=self.on_search_clicked, font=self.control_font
        )
        self.search_button.pack(pady=10)

        # Right side: map + results
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
        for widget in self.result_scrollable_frame.winfo_children():
            widget.destroy()

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

        # route type => direct=0, one_stop=1, two_stop=2
        route_type = self.route_type_var.get()
        if route_type == "direct":
            stops = 0
        elif route_type == "one_stop":
            stops = 1
        else:
            stops = 2

        filter_choice = self.filter_var.get()
        cabin_choice = self.cabin_var.get()

        # Parse the currency code from "SGD - Singapore Dollar"
        cur_selection = self.currency_var.get().split(" - ")[0]  # e.g. "USD"

        if trip_type == "one_way":
            routes = algorithms.find_one_way_flights(
                graph=airport_graph,
                departure=departure,
                destination=destination,
                stops=stops,
                filter_type=filter_choice,
                cabin=cabin_choice
            )
            self.display_routes(routes, cur_selection)
        else:
            if len(mid_raw) < 2:
                self.show_message("Invalid Middle Airport.")
                self.draw_map()
                return
            middle = mid_raw[0]

            routes_dep_mid = algorithms.find_one_way_flights(
                graph=airport_graph,
                departure=departure,
                destination=middle,
                stops=stops,
                filter_type=filter_choice,
                cabin=cabin_choice
            )
            routes_mid_dest = algorithms.find_one_way_flights(
                graph=airport_graph,
                departure=middle,
                destination=destination,
                stops=stops,
                filter_type=filter_choice,
                cabin=cabin_choice
            )

            merged_routes = []
            for (r1, d1, t1, c1, cab1) in routes_dep_mid:
                for (r2, d2, t2, c2, cab2) in routes_mid_dest:
                    combined_path = r1[:-1] + r2
                    total_dist = d1 + d2
                    total_time = t1 + t2
                    total_cost = c1 + c2
                    merged_routes.append((combined_path, total_dist, total_time, total_cost, cabin_choice))

            if filter_choice == "cheapest":
                merged_routes.sort(key=lambda x: x[3])
            else:
                merged_routes.sort(key=lambda x: x[2])

            self.display_routes(merged_routes, cur_selection)

    def show_message(self, msg):
        tk.Label(self.result_scrollable_frame, text=msg, font=self.control_font).pack(fill=tk.X, padx=5, pady=2)

    def display_routes(self, routes, currency_code):
        if not routes:
            self.show_message("No flights found.")
            self.draw_map()
            return

        first_route = routes[0][0]
        self.draw_map(route=first_route)

        # Retrieve the currency's "symbol" (which is actually code) & rate
        if currency_code not in currency_rates:
            currency_code = "SGD"
        code_string = currency_rates[currency_code]["symbol"]  # e.g. "USD"
        rate = currency_rates[currency_code]["rate"]

        for (routelist, dist, timing, cost_sgd, cabin) in routes:
            cost_converted = cost_sgd * rate

            segments = []
            for airport in routelist:
                airport_name = airport_data[airport]["name"]
                segments.append(f"{airport} ({airport_name})")
            route_line = " -> ".join(segments)

            display_str = (
                f"{route_line}\n"
                f"  Total Distance: {dist} km\n"
                f"  Total Timing: {timing} min\n"
                f"  Price: {code_string}{cost_converted:.2f} ({cabin})"
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
