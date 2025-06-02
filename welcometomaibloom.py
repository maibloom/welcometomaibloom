import sys
from PyQt5.QtWidgets import (
    QApplication, QWizard, QWizardPage, QVBoxLayout, QHBoxLayout,
    QLabel, QCheckBox, QPushButton, QMessageBox, QInputDialog, QLineEdit, QTextEdit
)
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, QProcess, QCoreApplication

# Simplified mapping: User-friendly name to package name
PACKAGE_MAPPING = {
    "Education": "maibloom-edupackage",
    "Programming": "maibloom-devpackage",
    "Office": "maibloom-officepackage",
    "Daily Use": "maibloom-dailypackage",
    "Gaming": "maibloom-gamingpackage"
}

# Helper to safely load pixmaps
def load_pixmap(path, default_size=(150,150)):
    pixmap = QPixmap(path)
    if pixmap.isNull():
        print(f"Warning: Could not load image at {path}. Using a placeholder.")
        # Create a placeholder pixmap
        placeholder = QPixmap(default_size[0], default_size[1])
        placeholder.fill(Qt.lightGray)
        return placeholder
    return pixmap

class IntroPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Welcome to Mai Bloom OS Setup")
        self.setSubTitle("Select the packages you want to install based on your daily needs:")
        layout = QVBoxLayout()

        logo_label = QLabel()
        logo_pixmap = load_pixmap("logo.png", (150,150))
        logo_label.setPixmap(logo_pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)

        self.checkboxes = {}
        for option in PACKAGE_MAPPING.keys():
            cb = QCheckBox(option)
            self.checkboxes[option] = cb
            layout.addWidget(cb)
        self.setLayout(layout)

    def get_selected_package_names(self):
        selected_names = []
        for option, cb in self.checkboxes.items():
            if cb.isChecked():
                selected_names.append(PACKAGE_MAPPING[option])
        return sorted(selected_names) # Sorted for consistent comparison

class CommandPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Installing Packages")
        self.setSubTitle("The installation command will now execute and output will be shown in real time.")
        
        layout = QVBoxLayout()
        self.output_view = QTextEdit()
        self.output_view.setReadOnly(True)
        self.output_view.setLineWrapMode(QTextEdit.WidgetWidth) # Ensure text wraps
        layout.addWidget(self.output_view)
        self.setLayout(layout)

        self.process = None
        self._password_to_use = None # Store password temporarily
        self._is_complete = False
        self._installation_running = False
        self._current_packages_str_for_run = "" # To track what's being/been installed

    def initializePage(self):
        # This method is called each time the page is shown.
        intro_page = self.wizard().page(self.wizard().pageIds()[0]) # Assuming IntroPage is the first page (ID 0)
        selected_package_names = intro_page.get_selected_package_names()
        current_packages_str = " ".join(selected_package_names)

        if self._installation_running:
            # Installation is already in progress, do nothing.
            # Buttons should already be in the correct (disabled) state.
            return

        if self._is_complete and self._current_packages_str_for_run == current_packages_str:
            # Already completed successfully for these exact packages.
            # The log is already in output_view. Ensure buttons are correct.
            self.wizard().button(QWizard.BackButton).setEnabled(True)
            # self.completeChanged.emit() will ensure Next/Finish is enabled.
            return # No need to re-run or clear

        # If we reach here, it's a new installation, a retry, or selections changed.
        self.output_view.clear()
        self._is_complete = False
        self._current_packages_str_for_run = current_packages_str # Store for this attempt
        self.completeChanged.emit() # Disable Next/Finish button initially

        if not selected_package_names:
            self.output_view.setPlainText("No packages were selected. Nothing to install.")
            self._is_complete = True # Vacuously true, can proceed.
            self.completeChanged.emit()
            return

        full_command = f"sudo -S omnipkg put install {current_packages_str}"
        self.output_view.append(f"Preparing to execute: {full_command}\n")

        # Only ask for password if we are actually going to run a command
        # A more sophisticated approach might cache the password for a short duration
        # or use a dedicated password management utility if available.
        password, ok = QInputDialog.getText(
            self, "Sudo Password", "Please enter your sudo password:", QLineEdit.Password
        )

        if not ok or not password:
            self.output_view.append("Sudo password not provided. Aborting execution.")
            # _is_complete remains False, user cannot proceed without password for installations.
            # They can go back to change selections or retry.
            self.wizard().button(QWizard.BackButton).setEnabled(True)
            self.completeChanged.emit()
            return

        self._password_to_use = password

        if self.process: # Clean up old process if any (should not happen with current logic)
            self.process.kill()
            self.process.waitForFinished(1000)

        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.handle_output)
        self.process.finished.connect(self.command_finished) # exitCode, exitStatus
        self.process.errorOccurred.connect(self.handle_process_error) # QProcess.ProcessError
        self.process.started.connect(self._feed_password_to_process)

        self.output_view.append("Starting installation...\n")
        
        # Disable navigation buttons during installation
        self.wizard().button(QWizard.BackButton).setEnabled(False)
        self.wizard().button(QWizard.NextButton).setEnabled(False) # Also handles FinishButton
        self.wizard().button(QWizard.CancelButton).setEnabled(False)


        self._installation_running = True
        self.process.start(full_command) # program, arguments_list
        
        # Check if starting the process itself failed (e.g. command not found)
        # QProcess.start() is non-blocking. errorOccurred handles this.

    def _feed_password_to_process(self):
        if self.process and self._password_to_use:
            self.process.write((self._password_to_use + "\n").encode(errors='replace'))
            self.process.closeWriteChannel() # Important after sending password via sudo -S
            self._password_to_use = None # Clear password from memory

    def handle_output(self):
        if not self.process: return
        # StandardOutput often contains both stdout and stderr when MergedChannels is used
        data = self.process.readAllStandardOutput().data().decode(errors="replace")
        self.output_view.append(data)
        self.output_view.ensureCursorVisible()

    def handle_process_error(self, error: QProcess.ProcessError):
        # This catches errors like "FailedToStart" (command not found, permissions issues)
        if not self.process: return
        self.output_view.append(f"\nProcess Error: {self.process.errorString()}\n")
        # command_finished will usually still be called, even after FailedToStart
        # We let command_finished handle the final state update.

    def command_finished(self, exitCode, exitStatus: QProcess.ExitStatus):
        # This signal is emitted when the process finishes, either normally or due to a crash/error.
        self._installation_running = False

        # Re-enable navigation buttons
        self.wizard().button(QWizard.BackButton).setEnabled(True)
        self.wizard().button(QWizard.CancelButton).setEnabled(True)


        if exitStatus == QProcess.CrashExit:
            self.output_view.append("\nInstallation process crashed.\n")
            self._is_complete = False
        elif exitCode != 0:
            self.output_view.append(f"\nInstallation failed with exit code: {exitCode}.\n")
            # You could add more specific error messages based on common exit codes if known.
            self._is_complete = False
        else:
            self.output_view.append("\nInstallation completed successfully.\n")
            self._is_complete = True
        
        self.completeChanged.emit() # This will update the Next/Finish button state

    def isComplete(self):
        # This determines if the "Next" or "Finish" button is enabled.
        return self._is_complete

    def cleanupPage(self):
        # Called when navigating away from this page.
        # If installation is running and user somehow navigates away (e.g. cancel),
        # you might want to terminate the process.
        if self._installation_running and self.process:
            self.output_view.append("\nWarning: Navigating away from active installation. Attempting to terminate...")
            self.process.kill() # Send SIGKILL
            if not self.process.waitForFinished(2000): # Wait up to 2s
                 self.output_view.append("\nProcess did not terminate gracefully.")
            else:
                 self.output_view.append("\nProcess terminated.")
            self._installation_running = False


class FinalPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Enjoy!")
        self.setSubTitle("Thank you for setting up Mai Bloom OS.")
        layout = QVBoxLayout()

        logo_label = QLabel()
        logo_pixmap = load_pixmap("logo.png", (100,100))
        logo_label.setPixmap(logo_pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)

        info_label = QLabel("Welcome to Mai Bloom OS!\n\nFeel free to exit or learn more about our OS.")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        button_layout = QHBoxLayout()
        self.exit_button = QPushButton("Exit")
        self.learn_more_button = QPushButton("Learn More")
        button_layout.addWidget(self.exit_button)
        button_layout.addWidget(self.learn_more_button)
        layout.addLayout(button_layout)
        self.setLayout(layout)

        self.exit_button.clicked.connect(self.exit_app)
        self.learn_more_button.clicked.connect(self.learn_more)

    def exit_app(self):
        QCoreApplication.instance().quit() # Correct way to quit app

    def learn_more(self):
        import webbrowser
        # Consider making the URL a constant or configurable
        try:
            webbrowser.open("https://example.com/maibloom") # Replace with actual URL
            QMessageBox.information(self, "Learn More", "Opening the Mai Bloom OS website in your browser.")
        except Exception as e:
            QMessageBox.warning(self, "Learn More Error", f"Could not open browser: {e}")

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet("""
        QWizard {
            background-color: #f8f8f8; /* Light gray background for the wizard window */
        }
        QWizardPage {
            background-color: white; /* White background for page content area */
            font-family: Arial, sans-serif;
            font-size: 10pt; /* Using points for better scalability */
        }
        QLabel#TitleLabel { /* Specific styling for title label if QWizard uses objectNames */
            font-size: 16pt;
            font-weight: bold;
        }
        QLabel#SubTitleLabel {
            font-size: 11pt;
            margin-bottom: 15px;
        }
        QLabel { /* General labels */
            margin: 5px;
            color: #333; /* Darker text color */
        }
        QCheckBox {
            margin: 8px 5px;
            font-size: 10pt;
        }
        QTextEdit {
            border: 1px solid #ccc;
            background-color: #fff;
            font-family: "Courier New", Courier, monospace; /* Monospaced font for output */
            font-size: 9pt;
            color: #222;
        }
        QPushButton {
            background-color: #007bff; /* A modern blue */
            color: white;
            border: none;
            padding: 10px 15px;
            margin: 10px 5px;
            font-size: 10pt;
            border-radius: 4px; /* Rounded corners */
        }
        QPushButton:hover {
            background-color: #0056b3; /* Darker blue on hover */
        }
        QPushButton:disabled {
            background-color: #c0c0c0; /* Gray when disabled */
            color: #666666;
        }
    """)

    wizard = QWizard()
    wizard.setWindowTitle("Mai Bloom OS Setup")
    wizard.setWindowIcon(QIcon(load_pixmap("logo.png", (32,32)))) # Use loaded pixmap for icon too

    # Adding pages and storing their IDs if needed for navigation (page IDs are 0, 1, 2...)
    intro_page_id = wizard.addPage(IntroPage())
    command_page_id = wizard.addPage(CommandPage())
    wizard.addPage(FinalPage())

    # Wizard style options
    wizard.setWizardStyle(QWizard.ModernStyle) # Or AeroStyle, MacStyle, ClassicStyle
    # wizard.setOption(QWizard.HaveHelpButton, True) # Example: If you add help
    # wizard.setPixmap(QWizard.LogoPixmap, load_pixmap("logo.png", (64,64))) # For sidebar logo

    wizard.resize(600, 450) # A reasonable default size
    wizard.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
