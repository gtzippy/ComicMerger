import os
import shutil
import subprocess
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import rarfile
import zipfile

class ComicMergerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Comic Merger")

        self.image_files = []
        self.selected_files = set()
        self.temp_dir = tempfile.mkdtemp()
        self.popup = None

        self.setup_ui()

    def setup_ui(self):
        # Buttons for opening archive and creating CBR
        button_frame = tk.Frame(self.root)
        button_frame.pack(side=tk.TOP, fill=tk.X)

        open_button = tk.Button(button_frame, text="Open Archives", command=self.open_archives)
        open_button.pack(side=tk.LEFT, padx=5, pady=5)

        create_button = tk.Button(button_frame, text="Create CBR", command=self.create_cbr)
        create_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Canvas for displaying images
        self.canvas = tk.Canvas(self.root)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar for the canvas
        self.scrollbar = tk.Scrollbar(self.root, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Frame inside the canvas to hold images
        self.image_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.image_frame, anchor="nw")
        self.image_frame.bind("<Configure>", self.update_scroll_region)

        # Bind mouse scroll to scroll the canvas
        self.canvas.bind_all("<MouseWheel>", self.on_mouse_scroll)

    def update_scroll_region(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_mouse_scroll(self, event):
        direction = -1 if event.delta > 0 else 1
        self.canvas.yview_scroll(direction, "units")

    def clear_temp_dir(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        self.temp_dir = tempfile.mkdtemp()

    def open_archives(self):
        file_paths = filedialog.askopenfilenames(filetypes=[
            ("Comic Archives", "*.cbr *.cbz *.rar *.zip"),
            ("All Files", "*.*")
        ])

        if not file_paths:
            return

        self.clear_temp_dir()

        try:
            for file_path in file_paths:
                if file_path.endswith(".cbr") or file_path.endswith(".rar"):
                    with rarfile.RarFile(file_path) as rf:
                        rf.extractall(self.temp_dir)
                elif file_path.endswith(".cbz") or file_path.endswith(".zip"):
                    with zipfile.ZipFile(file_path) as zf:
                        zf.extractall(self.temp_dir)
                else:
                    messagebox.showerror("Error", "Unsupported archive format.")
                    return
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open archive: {e}")
            return

        self.load_images()

    def load_images(self):
        for widget in self.image_frame.winfo_children():
            widget.destroy()

        self.image_files = [
            os.path.join(self.temp_dir, f) for f in sorted(os.listdir(self.temp_dir))
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".gif"))
        ]
        self.selected_files = set(self.image_files)

        for image_path in self.image_files:
            self.add_image_to_frame(image_path)

    def add_image_to_frame(self, image_path):
        frame = tk.Frame(self.image_frame)
        frame.pack(fill=tk.X, padx=5, pady=5)

        img = Image.open(image_path)
        img.thumbnail((150, 150))
        photo = ImageTk.PhotoImage(img)

        label = tk.Label(frame, image=photo)
        label.image = photo
        label.pack(side=tk.LEFT)

        checkbox_var = tk.BooleanVar(value=True)
        checkbox = tk.Checkbutton(frame, variable=checkbox_var)
        checkbox.pack(side=tk.RIGHT)

        def toggle_selection(event=None):
            if checkbox_var.get():
                checkbox_var.set(False)
                self.selected_files.discard(image_path)
            else:
                checkbox_var.set(True)
                self.selected_files.add(image_path)

        def show_popup(event):
            if self.popup:
                self.popup.destroy()
                self.popup = None

            img_large = Image.open(image_path)
            img_large.thumbnail((600, 600))
            popup_photo = ImageTk.PhotoImage(img_large)

            self.popup = tk.Toplevel(self.root)
            self.popup.geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
            self.popup.overrideredirect(True)

            popup_label = tk.Label(self.popup, image=popup_photo)
            popup_label.image = popup_photo
            popup_label.pack()

        def hide_popup(event):
            if self.popup:
                self.popup.destroy()
                self.popup = None

        label.bind("<Button-1>", toggle_selection)
        label.bind("<Button-2>", show_popup)
        label.bind("<ButtonRelease-2>", hide_popup)
        checkbox.bind("<Button-1>", toggle_selection)

    def create_cbr(self):
        if not self.selected_files:
            messagebox.showerror("Error", "No images selected to create the archive.")
            return

        save_path = filedialog.asksaveasfilename(defaultextension=".cbr", filetypes=[("CBR Files", "*.cbr")])
        if not save_path:
            return

        temp_output_dir = os.path.join(self.temp_dir, "output")
        os.makedirs(temp_output_dir, exist_ok=True)

        try:
            for idx, file_path in enumerate(sorted(self.selected_files)):
                ext = os.path.splitext(file_path)[1]
                new_name = f"{idx:03}{ext}"
                shutil.copy(file_path, os.path.join(temp_output_dir, new_name))

            rar_command = shutil.which("rar")
            if not rar_command:
                raise EnvironmentError("RAR utility not found. Please install it.")

            subprocess.run(
                [rar_command, "a", "-ep1", save_path, f"{temp_output_dir}/*"],
                check=True
            )

            messagebox.showinfo("Success", f"CBR archive created: {save_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create CBR archive: {e}")
        finally:
            shutil.rmtree(temp_output_dir, ignore_errors=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = ComicMergerApp(root)
    root.mainloop()
