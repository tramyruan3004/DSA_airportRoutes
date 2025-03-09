import tkinter as tk
import os
from tkinterweb import HtmlFrame

class MapApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Leaflet Map")

        # Create a frame for the HTML viewer
        self.frame = tk.Frame(self.root)
        self.frame.pack(fill=tk.BOTH, expand=True)

        # Load the map
        self.load_map()

    def load_map(self):
        html_path = os.path.abspath("index.html")
        file_url = f"file:///{html_path.replace(os.sep, '/')}"
        # Convert Windows paths

        # Create an HTML display frame
        self.html_frame = HtmlFrame(self.frame)
        self.html_frame.pack(fill=tk.BOTH, expand=True)

        # Debug: Print the file path
        print("Loading HTML from:", file_url)

        # Load the HTML file
        self.html_frame.load_url(file_url)

if __name__ == "__main__":
    root = tk.Tk()
    app = MapApp(root)
    root.mainloop()
