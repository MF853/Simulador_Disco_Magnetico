import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random

class DiskSchedulingSimulator:
    """
    A GUI application to simulate and visualize various disk scheduling algorithms.
    All algorithm results are plotted in a single window for comparison.
    """

    def __init__(self, master):
        """
        Initializes the simulator application.

        Args:
            master: The root Tkinter window.
        """
        self.master = master
        self.master.title("Disk Scheduling Algorithm Simulator")
        self.master.geometry("800x800")  # Adjusted for single plot window
        self.master.protocol("WM_DELETE_WINDOW", self._on_closing)

        # --- Frames for layout ---
        top_frame = ttk.Frame(self.master, padding="10")
        top_frame.pack(pady=5, padx=10, fill="x", side="top")

        plot_frame = ttk.Frame(self.master, padding="10")
        plot_frame.pack(pady=5, padx=10, fill="both", expand=True)

        # --- Input fields in top_frame ---
        control_frame = ttk.Frame(top_frame)
        control_frame.pack()

        ttk.Label(control_frame, text="Initial Head Position:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.head_var = tk.StringVar(value="50")
        ttk.Entry(control_frame, textvariable=self.head_var, width=10).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(control_frame, text="Max Cylinder:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.disk_size_var = tk.StringVar(value="200")
        ttk.Entry(control_frame, textvariable=self.disk_size_var, width=10).grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(control_frame, text="Request Queue (comma-separated):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.requests_var = tk.StringVar(value="98,183,37,122,14,124,65,67")
        ttk.Entry(control_frame, textvariable=self.requests_var, width=50).grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky="we")

        # --- Random queue generation ---
        random_frame = ttk.Frame(control_frame)
        random_frame.grid(row=2, column=0, columnspan=4, pady=5)

        ttk.Label(random_frame, text="Number of Random Requests:").pack(side="left", padx=(0, 5))
        self.random_count_var = tk.StringVar(value="8")
        ttk.Entry(random_frame, textvariable=self.random_count_var, width=5).pack(side="left")
        ttk.Button(random_frame, text="Generate Random Queue", command=self.generate_random_queue).pack(side="left", padx=5)

        # --- Buttons ---
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=3, column=0, columnspan=4, pady=(10, 0))
        ttk.Button(button_frame, text="Run Simulation", command=self.run_simulation).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Clear Plot", command=self.clear_plot).pack(side="left", padx=5)

        # --- Matplotlib plot area ---
        # Create a figure with 5 subplots, sharing the X-axis
        self.fig, self.axs = plt.subplots(5, 1, figsize=(10, 12), sharex=True)
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.fig.suptitle("Disk Scheduling Algorithm Comparison", fontsize=16)


    def _on_closing(self):
        """Handles the window closing event to ensure a clean exit."""
        plt.close('all')
        self.master.destroy()


    def clear_plot(self):
        """Clears all subplots."""
        for ax in self.axs:
            ax.clear()
        self.fig.suptitle("Disk Scheduling Algorithm Comparison", fontsize=16) # Reset title
        self.canvas.draw()


    def generate_random_queue(self):
        """Generates a random queue of disk requests."""
        try:
            disk_size = int(self.disk_size_var.get())
            count = int(self.random_count_var.get())
            if count >= disk_size:
                messagebox.showerror("Error", "Number of random requests must be less than the disk size.")
                return

            requests = random.sample(range(disk_size), count)
            self.requests_var.set(','.join(map(str, requests)))

        except ValueError:
            messagebox.showerror("Error", "Please enter valid integers for Disk Size and Number of Random Requests.")


    def get_inputs(self):
        """Retrieves and validates user inputs."""
        try:
            head = int(self.head_var.get())
            disk_size = int(self.disk_size_var.get())
            requests_str = self.requests_var.get().strip()

            if not requests_str:
                messagebox.showerror("Error", "Request Queue cannot be empty.")
                return None

            requests = [int(r.strip()) for r in requests_str.split(',')]

            if not (0 <= head < disk_size):
                messagebox.showerror("Error", f"Initial head position ({head}) must be in [0, {disk_size-1}].")
                return None

            if any(not (0 <= r < disk_size) for r in requests):
                 messagebox.showerror("Error", f"All requests must be in [0, {disk_size-1}].")
                 return None

            return head, requests, disk_size
        except (ValueError, TypeError):
            messagebox.showerror("Error", "Please enter valid integer values for all fields.")
            return None
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
            return None


    def run_simulation(self):
        """Runs the simulation and plots results on the shared canvas."""
        inputs = self.get_inputs()
        if not inputs:
            return

        self.clear_plot()
        head, requests, disk_size = inputs

        algorithms = {
            "FCFS": (self.fcfs, self.axs[0]),
            "SSTF": (self.sstf, self.axs[1]),
            "SCAN": (self.scan, self.axs[2]),
            "C-SCAN": (self.c_scan, self.axs[3]),
            "C-LOOK": (self.c_look, self.axs[4])
        }

        for name, (func, ax) in algorithms.items():
            seek_sequence, total_seek = func(head, list(requests), disk_size)
            self.plot_on_axis(ax, name, seek_sequence, total_seek, disk_size)
        
        # Set common X-label for the last subplot
        self.axs[-1].set_xlabel("Cylinder / Track Number", fontsize=12)
        self.fig.tight_layout(rect=[0, 0.03, 1, 0.95]) # Adjust layout to make room for suptitle
        self.canvas.draw()


    def plot_on_axis(self, ax, name, sequence, total_seek, disk_size):
        """
        Plots the disk head's movement on a specific subplot axis.
        """
        y_coords = list(range(len(sequence)))
        ax.plot(sequence, y_coords, '-o', color='blue', markersize=6, markerfacecolor='lightblue')
        ax.invert_yaxis()

        if name in ["SCAN", "C-SCAN", "C-LOOK"]:
            for i in range(len(sequence) - 1):
                x1, y1, x2, y2 = sequence[i], y_coords[i], sequence[i+1], y_coords[i+1]
                ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                            arrowprops=dict(arrowstyle="->", color="r", shrinkA=4, shrinkB=4))

        ax.set_yticks(y_coords)
        ax.set_yticklabels(sequence)
        ax.set_ylabel("Request Order")
        ax.set_title(f"{name} (Total Seek: {total_seek})")
        ax.set_xlim(-5, disk_size + 5)
        ax.grid(True, linestyle='--', alpha=0.6)


    # --- Disk Scheduling Algorithms ---
    def fcfs(self, head, requests, disk_size):
        seek_sequence = [head] + requests
        total_seek = sum(abs(seek_sequence[i] - seek_sequence[i-1]) for i in range(1, len(seek_sequence)))
        return seek_sequence, total_seek

    def sstf(self, head, requests, disk_size):
        current_head, seek_sequence = head, [head]
        while requests:
            closest_req = min(requests, key=lambda x: abs(x - current_head))
            current_head = closest_req
            seek_sequence.append(current_head)
            requests.remove(current_head)
        total_seek = sum(abs(seek_sequence[i] - seek_sequence[i-1]) for i in range(1, len(seek_sequence)))
        return seek_sequence, total_seek

    def scan(self, head, requests, disk_size, direction="right"):
        seek_sequence = [head]
        requests.sort()
        if direction == "right":
            right = [r for r in requests if r >= head]
            left = [r for r in requests if r < head]
            seek_sequence.extend(right)
            if left:
                seek_sequence.append(disk_size - 1)
                seek_sequence.extend(sorted(left, reverse=True))
        else: # "left"
            left = [r for r in requests if r < head]
            right = [r for r in requests if r >= head]
            seek_sequence.extend(sorted(left, reverse=True))
            if right:
                seek_sequence.append(0)
                seek_sequence.extend(right)
        total_seek = sum(abs(seek_sequence[i] - seek_sequence[i-1]) for i in range(1, len(seek_sequence)))
        return seek_sequence, total_seek

    def c_scan(self, head, requests, disk_size):
        seek_sequence = [head]
        requests.sort()
        right = [r for r in requests if r >= head]
        left = [r for r in requests if r < head]
        seek_sequence.extend(right)
        if left:
            seek_sequence.extend([disk_size - 1, 0])
            seek_sequence.extend(left)
        total_seek = sum(abs(seek_sequence[i] - seek_sequence[i-1]) for i in range(1, len(seek_sequence)))
        return seek_sequence, total_seek

    def c_look(self, head, requests, disk_size):
        seek_sequence = [head]
        requests.sort()
        right = [r for r in requests if r >= head]
        left = [r for r in requests if r < head]
        seek_sequence.extend(right)
        if left:
            seek_sequence.extend(left)
        total_seek = sum(abs(seek_sequence[i] - seek_sequence[i-1]) for i in range(1, len(seek_sequence)))
        return seek_sequence, total_seek


if __name__ == "__main__":
    root = tk.Tk()
    app = DiskSchedulingSimulator(root)
    root.mainloop()