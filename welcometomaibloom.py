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
        container = ctk.CTkFrame(self)
        container.pack(side="top", fill="both", expand=True)
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
        super().__init__(parent)
        self.controller = controller

        # Load the logo from /usr/local/bin/welcometomaibloom/logo.png
        self.logo_image = tk.PhotoImage(file="/usr/local/bin/welcometomaibloom/logo.png")
        self.logo_label = ctk.CTkLabel(self, image=self.logo_image, text="")
        self.logo_label.pack(pady=20)

        self.title_label = ctk.CTkLabel(self, text="Welcome to Mai Bloom OS Setup", font=("Arial", 20))
        self.title_label.pack(pady=10)
        self.subtitle_label = ctk.CTkLabel(
            self,
            text="Select the packages you want to install based on your daily needs:",
            font=("Arial", 14)
        )
        self.subtitle_label.pack(pady=10)

        self.options = ["Education", "Programming", "Office", "Daily Use", "Gaming"]
        self.checkbox_vars = {}
        for option in self.options:
            var = tk.BooleanVar()
            chk = ctk.CTkCheckBox(self, text=option, variable=var)
            chk.pack(anchor="w", padx=20, pady=5)
            self.checkbox_vars[option] = var

        self.next_button = ctk.CTkButton(self, text="Next", command=self.go_next)
        self.next_button.pack(pady=20)

    def go_next(self):
        selected = {option: var.get() for option, var in self.checkbox_vars.items()}
        self.controller.selected_packages = selected
        self.controller.show_frame("CommandPage")

    def on_show(self):
        pass

class CommandPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.title_label = ctk.CTkLabel(self, text="Installing Packages", font=("Arial", 20))
        self.title_label.pack(pady=10)
        self.subtitle_label = ctk.CTkLabel(self, text="Installation output:", font=("Arial", 14))
        self.subtitle_label.pack(pady=10)

        # CTkTextbox is used to show the output.
        self.text_output = ctk.CTkTextbox(self, width=700, height=300)
        self.text_output.pack(padx=20, pady=20)

        self.next_button = ctk.CTkButton(self, text="Next", command=self.go_next, state="disabled")
        self.next_button.pack(pady=10)

        self.process = None
        self.output_queue = queue.Queue()
        self.read_thread = None

    def on_show(self):
        self.text_output.delete("0.0", tk.END)
        self.next_button.configure(state="disabled")
        selected = self.controller.selected_packages
        selected_options = []
        for option, value in selected.items():
            if value:
                selected_options.append(OUTPUT_MAPPING[option])
        if not selected_options:
            self.text_output.insert(tk.END, "No packages selected. Nothing to install.\n")
            self.next_button.configure(state="normal")
            return
        packages_str = " ".join(selected_options)
        # Build the command as requested.
        self.command = f"sudo -S omnipkg put install {packages_str}"
        self.text_output.insert(tk.END, f"Executing: {self.command}\n")
        self.password = simpledialog.askstring("Sudo Password", "Please enter your sudo password:", show="*")
        if not self.password:
            self.text_output.insert(tk.END, "No password provided. Aborting execution.\n")
            self.next_button.configure(state="normal")
            return
        self.start_process()

    def start_process(self):
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
        self.read_thread = threading.Thread(target=self.read_process_output, daemon=True)
        self.read_thread.start()
        self.after(100, self.poll_queue)

    def read_process_output(self):
        for line in self.process.stdout:
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
        if self.process.poll() is None:
            self.after(100, self.poll_queue)
        else:
            self.next_button.configure(state="normal")

    def go_next(self):
        self.controller.show_frame("FinalPage")

class FinalPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.title_label = ctk.CTkLabel(self, text="Enjoy!", font=("Arial", 20))
        self.title_label.pack(pady=10)
        self.subtitle_label = ctk.CTkLabel(
            self, text="Thank you for setting up Mai Bloom OS.", font=("Arial", 14)
        )
        self.subtitle_label.pack(pady=10)

        # Load the logo from /usr/local/bin/welcometomaibloom/logo.png
        self.logo_image = tk.PhotoImage(file="/usr/local/bin/welcometomaibloom/logo.png")
        self.logo_label = ctk.CTkLabel(self, image=self.logo_image, text="")
        self.logo_label.pack(pady=20)

        self.exit_button = ctk.CTkButton(self, text="Exit", command=self.exit_app)
        self.exit_button.pack(pady=10)
        self.learn_more_button = ctk.CTkButton(self, text="Learn More", command=self.learn_more)
        self.learn_more_button.pack(pady=10)

    def exit_app(self):
        self.controller.destroy()

    def learn_more(self):
        import webbrowser
        webbrowser.open("https://example.com/maibloom")

if __name__ == "__main__":
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    app = App()
    app.mainloop()
