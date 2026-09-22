"""Small desktop GUI for calculating STL mesh volume in liters."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from stl_to_volume import calculate_volume


UNIT_TO_LITERS = {
    "millimeters": 1e-6,
    "centimeters": 1e-3,
    "meters": 1e3,
    "inches": 16.387064,
}


class VolumeApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("STL Volume Calculator")
        self.geometry("560x360")
        self.minsize(480, 320)

        self.selected_path = tk.StringVar(value="No STL selected")
        self.unit = tk.StringVar(value="millimeters")
        self.use_convex_hull = tk.BooleanVar(value=False)
        self.status = tk.StringVar(value="Upload an STL file to calculate its volume.")
        self.volume_result = tk.StringVar(value="-")
        self.liters_result = tk.StringVar(value="-")

        self._build_widgets()

    def _build_widgets(self) -> None:
        container = ttk.Frame(self, padding=28)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)

        ttk.Label(
            container,
            text="STL Volume Calculator",
            font=("Segoe UI", 20, "bold"),
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            container,
            text="Upload a mesh and get its volume in liters.",
        ).grid(row=1, column=0, pady=(4, 24), sticky="w")

        upload_frame = ttk.Frame(container)
        upload_frame.grid(row=2, column=0, sticky="ew")
        upload_frame.columnconfigure(0, weight=1)
        ttk.Label(upload_frame, textvariable=self.selected_path).grid(
            row=0, column=0, padx=(0, 12), sticky="w"
        )
        ttk.Button(upload_frame, text="Upload STL", command=self.select_file).grid(
            row=0, column=1
        )

        options_frame = ttk.LabelFrame(container, text="Mesh settings", padding=12)
        options_frame.grid(row=3, column=0, pady=20, sticky="ew")
        ttk.Label(options_frame, text="STL units:").grid(row=0, column=0, sticky="w")
        unit_menu = ttk.Combobox(
            options_frame,
            textvariable=self.unit,
            values=tuple(UNIT_TO_LITERS),
            state="readonly",
            width=16,
        )
        unit_menu.grid(row=0, column=1, padx=(8, 20), sticky="w")
        unit_menu.bind("<<ComboboxSelected>>", self.recalculate)
        ttk.Checkbutton(
            options_frame,
            text="Use convex hull for open meshes",
            variable=self.use_convex_hull,
            command=self.recalculate,
        ).grid(row=0, column=2, sticky="w")

        result_frame = ttk.Frame(container)
        result_frame.grid(row=4, column=0, sticky="ew")
        result_frame.columnconfigure(1, weight=1)
        ttk.Label(result_frame, text="Volume:").grid(row=0, column=0, sticky="w")
        ttk.Label(
            result_frame, textvariable=self.volume_result, font=("Segoe UI", 13, "bold")
        ).grid(row=0, column=1, padx=12, sticky="w")
        ttk.Label(result_frame, text="Liters:").grid(row=1, column=0, pady=(8, 0), sticky="w")
        ttk.Label(
            result_frame, textvariable=self.liters_result, font=("Segoe UI", 18, "bold")
        ).grid(row=1, column=1, padx=12, pady=(8, 0), sticky="w")

        ttk.Label(container, textvariable=self.status, wraplength=500).grid(
            row=5, column=0, pady=(22, 0), sticky="w"
        )

    def select_file(self) -> None:
        selected_file = filedialog.askopenfilename(
            title="Select an STL file",
            filetypes=(("STL files", "*.stl"), ("All files", "*.*")),
        )
        if selected_file:
            self.selected_path.set(Path(selected_file).name)
            self.file_path = Path(selected_file)
            self.recalculate()

    def recalculate(self, *_args: object) -> None:
        file_path = getattr(self, "file_path", None)
        if file_path is None:
            return

        closure = "convex-hull" if self.use_convex_hull.get() else "reject"
        try:
            cubic_volume = calculate_volume(file_path, closure)
        except (OSError, ValueError) as error:
            self.volume_result.set("-")
            self.liters_result.set("-")
            self.status.set(str(error))
            return

        liters = cubic_volume * UNIT_TO_LITERS[self.unit.get()]
        self.volume_result.set(f"{cubic_volume:,.6g} cubic {self.unit.get()}")
        self.liters_result.set(f"{liters:,.6g} L")
        self.status.set("Calculation complete.")


def main() -> None:
    try:
        app = VolumeApp()
        app.mainloop()
    except tk.TclError as error:
        messagebox.showerror("Unable to start GUI", str(error))


if __name__ == "__main__":
    main()