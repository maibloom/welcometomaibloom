import customtkinter as ctk
import tkinter as tk
from tkinter import simpledialog
import subprocess
import threading
import queue

# Mapping for output names.
OUTPUT_MAPPING = {
    "Education": "maibloom-edupackage",
    "Programming": "maibloom-edupackage",
    "Office": "maibloom-edupackage",
    "Daily Use": "maibloom-edupackage",
    "Gaming": "maibloom-edupackage"
}

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Welcome to Mai Bloom OS")
        self.geometry("800x600")
        self.selected_packages = {}
        # Main container frame with slight padding and rounded corners
        container = ctk.CTkFrame(self, corner_radius=10, fg_color="transparent")
        container.pack(side="top", fill="both", expand=True, padx=20, pady=20)
        self.frames = {}

        for F in (IntroPage, CommandPage, FinalPage):
            frame = F(parent=container, controller=self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame("IntroPage")

    def show_frame(self, frame_name):
        frame = self.frames[frame_name]
        frame.tkraise()
        if hasattr(frame, "on_show"):
            frame.on_show()

class IntroPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, corner_radius=10)
        self.controller = controller

        # Step indicator at the top
        self.step_label = ctk.CTkLabel(self, text="Step 1 of 3: Package Selection", font=("Helvetica", 16, "bold"))
        self.step_label.pack(pady=(20, 10))

        # Load and display logo if available, otherwise show a text-based header
        try:
            self.logo_image = tk.PhotoImage(file="logo.png")
            self.logo_label = ctk.CTkLabel(self, image=self.logo_image, text="")
            self.logo_label.pack(pady=(10, 20))
        except Exception:
            self.logo_label = ctk.CTkLabel(self, text="Mai Bloom OS", font=("Helvetica", 24, "bold"))
            self.logo_label.pack(pady=(10, 20))
            
        self.title_label = ctk.CTkLabel(self, text="Welcome to Mai Bloom OS Setup", font=("Helvetica", 20, "bold"))
        self.title_label.pack(pady=(10, 10))
        self.subtitle_label = ctk.CTkLabel(
            self,
            text="Select the packages you want to install based on your daily needs:",
            font=("Helvetica", 14)
        )
        self.subtitle_label.pack(pady=(5, 15))

        # Organize checkboxes in a separate frame with grid layout for clarity.
        self.checkbox_frame = ctk.CTkFrame(self)
        self.checkbox_frame.pack(pady=10, padx=20, fill="x")

        self.options = ["Education", "Programming", "Office", "Daily Use", "Gaming"]
        self.checkbox_vars = {}
        row = 0
        col = 0
        for option in self.options:
            var = tk.BooleanVar()
            chk = ctk.CTkCheckBox(self.checkbox_frame, text=option, variable=var, font=("Helvetica", 12))
            chk.grid(row=row, column=col, padx=10, pady=10, sticky="w")
            self.checkbox_vars[option] = var
            col += 1
            if col > 1:
                col = 0
                row += 1

        self.next_button = ctk.CTkButton(
            self, text="Next", command=self.go_next,
            fg_color="#4a7abc", hover_color="#3671a3",
            font=("Helvetica", 14)
        )
        self.next_button.pack(pady=(20, 10))

    def go_next(self):
        selected = {option: var.get() for option, var in self.checkbox_vars.items()}
        self.controller.selected_packages = selected
        self.controller.show_frame("CommandPage")

    def on_show(self):
        # Optionally refresh or reset any state if needed.
        pass

class CommandPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, corner_radius=10)
        self.controller = controller

        self.step_label = ctk.CTkLabel(self, text="Step 2 of 3: Installing Packages", font=("Helvetica", 16, "bold"))
        self.step_label.pack(pady=(20, 10))

        self.title_label = ctk.CTkLabel(self, text="Installing Packages", font=("Helvetica", 20, "bold"))
        self.title_label.pack(pady=(10, 10))
        self.subtitle_label = ctk.CTkLabel(self, text="Installation output:", font=("Helvetica", 14))
        self.subtitle_label.pack(pady=(5, 10))

        self.text_output = ctk.CTkTextbox(self, width=700, height=250, font=("Helvetica", 12))
        self.text_output.pack(padx=20, pady=10)

        # Add an indeterminate progress bar to visually indicate activity.
        self.progress_bar = ctk.CTkProgressBar(self, width=700)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=(5, 10))
        
        # Frame to hold control buttons for improved layout.
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.pack(pady=(10, 20))

        self.cancel_button = ctk.CTkButton(
            self.button_frame, text="Cancel", command=self.cancel_process,
            fg_color="#c74b50", hover_color="#a03d42", font=("Helvetica", 14)
        )
        self.cancel_button.grid(row=0, column=0, padx=10)
        self.next_button = ctk.CTkButton(
            self.button_frame, text="Next", command=self.go_next,
            state="disabled", font=("Helvetica", 14)
        )
        self.next_button.grid(row=0, column=1, padx=10)

        self.process = None
        self.output_queue = queue.Queue()
        self.read_thread = None
        self.cancelled = False

    def on_show(self):
        self.text_output.delete("0.0", tk.END)
        self.progress_bar.set(0)
        self.next_button.configure(state="disabled")
        self.cancelled = False

        selected = self.controller.selected_packages
        selected_options = []
        for option, value in selected.items():
            if value:
                selected_options.append(OUTPUT_MAPPING[option])
        if not selected_options:
            self.text_output.insert(tk.END, "No packages selected. Nothing to install.\n")
            self.progress_bar.set(1)
            self.next_button.configure(state="normal")
            return

        packages_str = " ".join(selected_options)
        self.command = f"sudo -S omnipkg put install {packages_str}"
        self.text_output.insert(tk.END, f"Executing: {self.command}\n")
        self.password = simpledialog.askstring("Sudo Password", "Please enter your sudo password:", show="*")
        if not self.password:
            self.text_output.insert(tk.END, "No password provided. Aborting execution.\n")
            self.progress_bar.set(1)
            self.next_button.configure(state="normal")
            return
        self.start_process()

    def start_process(self):
        try:
            self.process = subprocess.Popen(
                self.command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            try:
                self.process.stdin.write(self.password + "\n")
                self.process.stdin.flush()
            except Exception as e:
                self.text_output.insert(tk.END, f"Error sending password: {e}\n")
            self.progress_bar.start()  # Begin the indeterminate progress indicator
            self.read_thread = threading.Thread(target=self.read_process_output, daemon=True)
            self.read_thread.start()
            self.after(100, self.poll_queue)
        except Exception as ex:
            self.text_output.insert(tk.END, f"Failed to start process: {ex}\n")
            self.progress_bar.set(1)
            self.next_button.configure(state="normal")

    def read_process_output(self):
        for line in self.process.stdout:
            if self.cancelled:
                break
            self.output_queue.put(line)
        err = self.process.stderr.read()
        if err:
            self.output_queue.put(err)
        self.process.stdout.close()
        self.process.stderr.close()
        self.process.wait()
        self.output_queue.put("[Process finished]\n")

    def poll_queue(self):
        try:
            while True:
                line = self.output_queue.get_nowait()
                self.text_output.insert(tk.END, line)
                self.text_output.see(tk.END)
        except queue.Empty:
            pass
        if self.process.poll() is None and not self.cancelled:
            self.after(100, self.poll_queue)
        else:
            self.progress_bar.stop()
            self.progress_bar.set(1)
            self.next_button.configure(state="normal")

    def cancel_process(self):
        if self.process and self.process.poll() is None:
            self.cancelled = True
            self.process.terminate()
            self.text_output.insert(tk.END, "\nInstallation cancelled by user.\n")
            self.next_button.configure(state="normal")
            self.progress_bar.stop()
            self.progress_bar.set(1)

    def go_next(self):
        self.controller.show_frame("FinalPage")

class FinalPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, corner_radius=10)
        self.controller = controller

        self.step_label = ctk.CTkLabel(self, text="Step 3 of 3: Completion", font=("Helvetica", 16, "bold"))
        self.step_label.pack(pady=(20, 10))

        self.title_label = ctk.CTkLabel(self, text="Enjoy!", font=("Helvetica", 20, "bold"))
        self.title_label.pack(pady=(10, 10))
        self.subtitle_label = ctk.CTkLabel(
            self, text="Thank you for setting up Mai Bloom OS.", font=("Helvetica", 14)
        )
        self.subtitle_label.pack(pady=(5, 15))

        try:
            self.logo_image = tk.PhotoImage(file="logo.png")
            self.logo_label = ctk.CTkLabel(self, image=self.logo_image, text="")
            self.logo_label.pack(pady=(10, 20))
        except Exception:
            self.logo_label = ctk.CTkLabel(self, text="Mai Bloom OS", font=("Helvetica", 20, "bold"))
            self.logo_label.pack(pady=(10, 20))

        # Layout for action buttons
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.pack(pady=20)
        
        self.learn_more_button = ctk.CTkButton(
            self.button_frame, text="Learn More", command=self.learn_more, font=("Helvetica", 14)
        )
        self.learn_more_button.grid(row=0, column=0, padx=10)
        self.exit_button = ctk.CTkButton(
            self.button_frame, text="Exit", command=self.exit_app,
            fg_color="#c74b50", hover_color="#a03d42", font=("Helvetica", 14)
        )
        self.exit_button.grid(row=0, column=1, padx=10)

    def exit_app(self):
        self.controller.destroy()

    def learn_more(self):
        import webbrowser
        webbrowser.open("https://www.maibloom.github.io")

if __name__ == "__main__":
    ctk.set_appearance_mode("light")  # Optionally switch to "dark"
    ctk.set_default_color_theme("blue")
    app = App()
    app.mainloop()
