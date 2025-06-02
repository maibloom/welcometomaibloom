import customtkinter
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk # Pillow for image handling
import subprocess
import threading
import queue
import sys
import os # For path joining
import webbrowser

# --- Constants and Mappings ---
PACKAGE_MAPPING = {
    "Education": "maibloom-edupackage",
    "Programming": "maibloom-devpackage",
    "Office": "maibloom-officepackage",
    "Daily Use": "maibloom-dailypackage",
    "Gaming": "maibloom-gamingpackage"
}

# --- Helper for Images ---
def load_ctk_image(path, size=(150, 150)):
    try:
        # Construct an absolute path if a relative path is given
        # Assuming 'logo.png' is in the same directory as the script
        if not os.path.isabs(path):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            path = os.path.join(script_dir, path)

        return customtkinter.CTkImage(light_image=Image.open(path),
                                     dark_image=Image.open(path),
                                     size=size)
    except FileNotFoundError:
        print(f"Warning: Could not load image at {path}. Using a placeholder.")
        # Create a placeholder PIL Image
        img = Image.new('RGB', size, color = 'lightgray')
        return customtkinter.CTkImage(light_image=img, dark_image=img, size=size)
    except Exception as e:
        print(f"Error loading image {path}: {e}")
        img = Image.new('RGB', size, color = 'lightgray')
        return customtkinter.CTkImage(light_image=img, dark_image=img, size=size)

# --- Page Base Class (Conceptual) ---
class WizardPage(customtkinter.CTkFrame):
    def __init__(self, master, wizard_app):
        super().__init__(master)
        self.wizard_app = wizard_app # To access wizard-level methods like navigation

    def get_title(self):
        return "Page Title" # Override in subclasses

    def get_subtitle(self):
        return "Page Subtitle" # Override in subclasses

    def on_show(self):
        """Called when page becomes visible. Replaces QWizardPage.initializePage()"""
        pass

    def on_hide(self):
        """Called when page is navigated away from. Replaces QWizardPage.cleanupPage()"""
        pass

    def is_complete(self):
        """Determines if 'Next' or 'Finish' can be enabled. Replaces QWizardPage.isComplete()"""
        return True # Default, override if conditions exist


# --- Intro Page ---
class IntroPage(WizardPage):
    def __init__(self, master, wizard_app):
        super().__init__(master, wizard_app)
        self.wizard_app = wizard_app

        self.title_label = customtkinter.CTkLabel(self, text="Welcome to Mai Bloom OS Setup", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.title_label.pack(pady=(10,5))

        self.subtitle_label = customtkinter.CTkLabel(self, text="Select the packages you want to install based on your daily needs:")
        self.subtitle_label.pack(pady=(0,20))

        self.logo_image = load_ctk_image("logo.png", (150, 150))
        self.logo_label = customtkinter.CTkLabel(self, image=self.logo_image, text="")
        self.logo_label.pack(pady=20)

        self.checkboxes = {}
        for option in PACKAGE_MAPPING.keys():
            cb = customtkinter.CTkCheckBox(self, text=option)
            cb.pack(anchor="w", padx=50, pady=5)
            self.checkboxes[option] = cb

    def get_title(self):
        return "Welcome"

    def get_selected_package_names(self):
        selected_names = []
        for option, cb in self.checkboxes.items():
            if cb.get() == 1: # CustomTkinter checkbox returns 1 for checked
                selected_names.append(PACKAGE_MAPPING[option])
        return sorted(selected_names)

# --- Command Page ---
class CommandPage(WizardPage):
    def __init__(self, master, wizard_app):
        super().__init__(master, wizard_app)
        self.wizard_app = wizard_app

        self.title_label = customtkinter.CTkLabel(self, text="Installing Packages", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.title_label.pack(pady=(10,5))

        self.subtitle_label = customtkinter.CTkLabel(self, text="The installation command will now execute and output will be shown.")
        self.subtitle_label.pack(pady=(0,10))

        self.output_view = customtkinter.CTkTextbox(self, height=200, width=500)
        self.output_view.pack(pady=10, padx=10, fill="both", expand=True)
        self.output_view.configure(state="disabled") # Read-only

        self._is_complete_flag = False
        self._installation_running = False
        self._current_packages_str_for_run = ""
        self.process_thread = None
        self.output_queue = queue.Queue()

    def get_title(self):
        return "Installation"

    def on_show(self):
        self.wizard_app.update_button_states() # Disable Next/Finish initially
        intro_page = self.wizard_app.pages[0] # Assuming IntroPage is the first
        selected_package_names = intro_page.get_selected_package_names()
        current_packages_str = " ".join(selected_package_names)

        if self._installation_running:
            return

        if self._is_complete_flag and self._current_packages_str_for_run == current_packages_str:
            self.wizard_app.update_button_states()
            return

        self.output_view.configure(state="normal")
        self.output_view.delete("1.0", "end")
        self.output_view.configure(state="disabled")

        self._is_complete_flag = False
        self._current_packages_str_for_run = current_packages_str
        self.wizard_app.update_button_states()

        if not selected_package_names:
            self._append_output("No packages were selected. Nothing to install.")
            self._is_complete_flag = True
            self.wizard_app.update_button_states()
            return

        full_command = f"sudo -S omnipkg put install {current_packages_str}"
        self._append_output(f"Preparing to execute: {full_command}\n")

        dialog = customtkinter.CTkInputDialog(text="Please enter your sudo password:", title="Sudo Password")
        password = dialog.get_input()


        if not password: # User cancelled or entered empty
            self._append_output("Sudo password not provided. Aborting execution.")
            self.wizard_app.update_button_states() # Should keep Next disabled
            return

        self._password_to_use = password
        self._installation_running = True
        self.wizard_app.set_navigation_enabled(False) # Disable nav buttons

        self._append_output("Starting installation...\n")

        self.process_thread = threading.Thread(target=self._run_command_thread, args=(full_command, self._password_to_use))
        self.process_thread.daemon = True # So it exits when main app exits
        self.process_thread.start()
        self.wizard_app.after(100, self._check_output_queue)

    def _append_output(self, text):
        self.output_view.configure(state="normal")
        self.output_view.insert("end", text)
        self.output_view.see("end")
        self.output_view.configure(state="disabled")

    def _run_command_thread(self, command, password):
        try:
            process = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
            
            # Send password to sudo -S
            process.stdin.write(password + '\n')
            process.stdin.flush()
            process.stdin.close() # Important for sudo -S

            for line in iter(process.stdout.readline, ''):
                self.output_queue.put(line)
            
            process.stdout.close()
            return_code = process.wait()
            self.output_queue.put(f"\n---PROCESS_FINISHED_CODE:{return_code}---\n")
        except Exception as e:
            self.output_queue.put(f"\n---PROCESS_ERROR:{str(e)}---\n")

    def _check_output_queue(self):
        try:
            while True:
                line = self.output_queue.get_nowait()
                if line.startswith("---PROCESS_FINISHED_CODE:"):
                    exit_code = int(line.split(":")[1].strip().replace("---", ""))
                    self._command_finished(exit_code)
                    return # Stop checking queue for this run
                elif line.startswith("---PROCESS_ERROR:"):
                    error_msg = line.replace("---PROCESS_ERROR:", "").replace("---", "").strip()
                    self._append_output(f"\nInstallation process error: {error_msg}\n")
                    self._command_finished(-1) # Indicate error
                    return
                else:
                    self._append_output(line)
        except queue.Empty:
            pass # No new output

        if self._installation_running:
            self.wizard_app.after(100, self._check_output_queue) # Poll again

    def _command_finished(self, exit_code):
        self._installation_running = False
        self.wizard_app.set_navigation_enabled(True) # Re-enable nav buttons

        if exit_code == 0:
            self._append_output("\nInstallation completed successfully.\n")
            self._is_complete_flag = True
        else:
            self._append_output(f"\nInstallation failed or process error (Code: {exit_code}).\n")
            self._is_complete_flag = False
        
        self.wizard_app.update_button_states()

    def is_complete(self):
        return self._is_complete_flag

    def on_hide(self):
        # Attempt to clean up if process is still somehow running when navigating away
        # This is a simplified cleanup. Robust cleanup of subprocesses can be complex.
        if self._installation_running and self.process_thread and self.process_thread.is_alive():
            self._append_output("\nWarning: Navigating away from active installation...\n")
            # Terminating threads directly is not recommended.
            # Ideally, the thread should check a flag to stop itself.
            # For subprocess, if we had direct access to 'process' object here, we could try process.terminate()
            print("Warning: Installation was running when navigating away from command page.")
            # For now, we assume the thread will complete or the app will close.
            # A more robust solution would involve a mechanism to signal the thread to stop,
            # and potentially `process.terminate()` or `process.kill()`.

# --- Final Page ---
class FinalPage(WizardPage):
    def __init__(self, master, wizard_app):
        super().__init__(master, wizard_app)
        self.wizard_app = wizard_app

        self.title_label = customtkinter.CTkLabel(self, text="Enjoy!", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.title_label.pack(pady=(10,5))

        self.subtitle_label = customtkinter.CTkLabel(self, text="Thank you for setting up Mai Bloom OS.")
        self.subtitle_label.pack(pady=(0,20))

        self.logo_image = load_ctk_image("logo.png", (100, 100))
        self.logo_label = customtkinter.CTkLabel(self, image=self.logo_image, text="")
        self.logo_label.pack(pady=20)

        info_text = "Welcome to Mai Bloom OS!\n\nFeel free to exit or learn more about our OS."
        self.info_label = customtkinter.CTkLabel(self, text=info_text, wraplength=400)
        self.info_label.pack(pady=10)

        button_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=20)

        self.exit_button = customtkinter.CTkButton(button_frame, text="Exit", command=self.exit_app)
        self.exit_button.pack(side="left", padx=10)

        self.learn_more_button = customtkinter.CTkButton(button_frame, text="Learn More", command=self.learn_more)
        self.learn_more_button.pack(side="left", padx=10)

    def get_title(self):
        return "Finished"

    def exit_app(self):
        self.wizard_app.destroy()

    def learn_more(self):
        url = "https://example.com/maibloom" # Replace with actual URL
        try:
            webbrowser.open(url)
            messagebox.showinfo("Learn More", f"Opening {url} in your browser.")
        except Exception as e:
            messagebox.showwarning("Learn More Error", f"Could not open browser: {e}")

# --- Main Application (Wizard Controller) ---
class MaiBloomWizard(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Mai Bloom OS Setup")
        self.geometry("700x600")
        # self.iconbitmap("logo.ico") # For .ico or .xbm. CTkImage might be used differently for window icon
        
        # Attempt to set window icon using CTkImage (might need a .ico or .xbm for older systems/Tkinter versions)
        # For a proper icon, you might need to save the logo as .ico and use self.iconbitmap()
        # CTk doesn't directly handle window icons via CTkImage in the same way Qt does.
        # For simplicity, this might be omitted or require platform-specific handling.
        try:
            icon_path_abs = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
            if os.path.exists(icon_path_abs):
                 # This is more for images within widgets. For window icon:
                 # self.iconphoto(True, tk.PhotoImage(file=icon_path_abs)) # Standard Tkinter way
                 # Or create an .ico and use self.iconbitmap("logo.ico")
                 pass # Window icon setting can be tricky cross-platform with just PNGs for root Tk window.
        except Exception as e:
            print(f"Could not set window icon: {e}")


        self.current_page_index = 0
        self.pages = []

        # Page container
        self.page_container = customtkinter.CTkFrame(self, fg_color="transparent")
        self.page_container.pack(pady=20, padx=20, fill="both", expand=True)

        # Create and add pages
        self._add_page(IntroPage)
        self._add_page(CommandPage)
        self._add_page(FinalPage)

        # Navigation buttons
        self.nav_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.nav_frame.pack(pady=10, padx=20, fill="x")

        self.cancel_button = customtkinter.CTkButton(self.nav_frame, text="Cancel", command=self.close_wizard)
        self.cancel_button.pack(side="left", padx=10)

        # Spacer to push other buttons to the right
        spacer = customtkinter.CTkFrame(self.nav_frame, fg_color="transparent", width=10) # Adjust width as needed
        spacer.pack(side="left", expand=True, fill="x")


        self.back_button = customtkinter.CTkButton(self.nav_frame, text="Back", command=self.go_back)
        self.back_button.pack(side="left", padx=5)

        self.next_button = customtkinter.CTkButton(self.nav_frame, text="Next", command=self.go_next)
        self.next_button.pack(side="left", padx=(5,0)) # No padx on right for finish button

        self.finish_button = customtkinter.CTkButton(self.nav_frame, text="Finish", command=self.close_wizard)
        self.finish_button.pack(side="left", padx=0)


        self.show_page(0)

    def _add_page(self, PageClass):
        page = PageClass(self.page_container, self)
        self.pages.append(page)
        # Initially hide all pages; show_page will manage visibility
        page.pack_forget() 

    def show_page(self, page_index):
        if 0 <= page_index < len(self.pages):
            # Hide current page if any
            if self.pages[self.current_page_index] is not self.pages[page_index] or not self.pages[self.current_page_index].winfo_ismapped():
                 current_page_widget = self.pages[self.current_page_index]
                 current_page_widget.on_hide()
                 current_page_widget.pack_forget()

            self.current_page_index = page_index
            new_page_widget = self.pages[self.current_page_index]
            
            new_page_widget.pack(fill="both", expand=True)
            new_page_widget.on_show() # Call on_show hook

            self.update_window_title()
            self.update_button_states()

    def update_window_title(self):
        current_page_widget = self.pages[self.current_page_index]
        # self.title(f"Mai Bloom OS Setup - {current_page_widget.get_title()}") # Update window title per page if desired

    def update_button_states(self):
        current_page_widget = self.pages[self.current_page_index]
        can_go_next = current_page_widget.is_complete()

        self.back_button.configure(state="normal" if self.current_page_index > 0 else "disabled")
        
        if self.current_page_index == len(self.pages) - 1: # Last page
            self.next_button.pack_forget() # Hide Next
            self.finish_button.pack(side="left", padx=0) # Show Finish
            self.finish_button.configure(state="normal" if can_go_next else "disabled")
        else:
            self.finish_button.pack_forget() # Hide Finish
            self.next_button.pack(side="left", padx=(5,0)) # Show Next
            self.next_button.configure(state="normal" if can_go_next else "disabled")
        
        # If the page itself controls completion (e.g. installation running)
        # it might also temporarily disable nav buttons.
        # The CommandPage does this by calling self.wizard_app.set_navigation_enabled()


    def set_navigation_enabled(self, enabled_state):
        state = "normal" if enabled_state else "disabled"
        self.back_button.configure(state=state if self.current_page_index > 0 else "disabled")
        self.cancel_button.configure(state=state)
        
        # Only touch next/finish if they are currently visible based on page index
        if self.current_page_index == len(self.pages) - 1: # Last page
            self.finish_button.configure(state=state)
        else:
            self.next_button.configure(state=state)


    def go_next(self):
        if self.current_page_index < len(self.pages) - 1:
            self.show_page(self.current_page_index + 1)

    def go_back(self):
        if self.current_page_index > 0:
            self.show_page(self.current_page_index - 1)

    def close_wizard(self):
        # Maybe ask for confirmation if CommandPage is running
        command_page_index = 1 # Assuming CommandPage is the second page
        if self.current_page_index == command_page_index:
            command_page_widget = self.pages[command_page_index]
            if command_page_widget._installation_running:
                if not messagebox.askyesno("Confirm Exit", "Installation is in progress. Are you sure you want to exit?"):
                    return
        self.destroy()


def main():
    customtkinter.set_appearance_mode("System")  # Modes: "System" (default), "Dark", "Light"
    customtkinter.set_default_color_theme("blue")  # Themes: "blue" (default), "green", "dark-blue"

    app = MaiBloomWizard()
    app.mainloop()

if __name__ == "__main__":
    main()
