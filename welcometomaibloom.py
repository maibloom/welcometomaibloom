#!/usr/bin/env python3
import sys
from PyQt5.QtWidgets import (
    QApplication, QWizard, QWizardPage, QLabel, QVBoxLayout, QHBoxLayout,
    QCheckBox, QLineEdit, QTextEdit, QPushButton, QMessageBox, QWidget, QDialog,
    QSizePolicy
)
from PyQt5.QtCore import QProcess, pyqtSlot, Qt
from PyQt5.QtGui import QFont

# --- Page IDs ---
class PageIds:
    WELCOME = 0
    INSTALL_SELECT = 1
    END = 2

# --- Welcome Page ---
class WelcomePage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Welcome to Mai Bloom!")
        self.setSubTitle("Click 'Next' to customize your OS.")
        
        layout = QVBoxLayout(self)
        lbl = QLabel("Welcome to Mai Bloom!\n\nYour journey towards a personalized OS begins here.")
        lbl.setFont(QFont("Arial", 16, QFont.Bold))
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setWordWrap(True)
        layout.addWidget(lbl)
        self.setLayout(layout)

    def nextId(self) -> int:
        return PageIds.INSTALL_SELECT

# --- Installation and Selection Page ---
class InstallSelectPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Package Selection and Installation")
        self.setSubTitle("Select packages, then click 'Next' to review and start installation.")

        # State flags
        self._installation_triggered_for_current_session = False # True once user confirms and installation starts
        self._installation_process_has_finished = False      # True once QProcess finishes (success or fail)
        self._selected_packages_for_install = []             # Stores confirmed packages for the current run

        self.page_layout = QVBoxLayout(self)

        # --- Selection Group ---
        self.selection_group_widget = QWidget()
        selection_layout = QVBoxLayout(self.selection_group_widget)
        info_label = QLabel("Select the package groups you want to install:")
        info_label.setFont(QFont("Arial", 12))
        info_label.setWordWrap(True)
        selection_layout.addWidget(info_label)

        self.package_options = ["Education", "Programming", "Office", "Daily Use", "Gaming"]
        self.checkboxes = {}
        for opt in self.package_options:
            cb = QCheckBox(opt)
            cb.setFont(QFont("Arial", 10))
            selection_layout.addWidget(cb)
            self.checkboxes[opt] = cb
        
        self.custom_input_label = QLabel("Enter additional package names (optional, space-separated):")
        selection_layout.addWidget(self.custom_input_label)
        self.custom_input_lineedit = QLineEdit()
        self.custom_input_lineedit.setPlaceholderText("e.g., custom-tool another-app")
        selection_layout.addWidget(self.custom_input_lineedit)
        self.page_layout.addWidget(self.selection_group_widget)

        # --- Log Group ---
        self.log_display_widget = QWidget()
        log_layout = QVBoxLayout(self.log_display_widget)
        log_label = QLabel("Installation Log:")
        log_label.setFont(QFont("Arial", 12))
        log_layout.addWidget(log_label)
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setFontFamily("Courier")
        self.log_text_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # Ensure it expands
        log_layout.addWidget(self.log_text_edit)
        self.page_layout.addWidget(self.log_display_widget)

        # --- QProcess Setup ---
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self._handle_stdout)
        self.process.readyReadStandardError.connect(self._handle_stderr)
        self.process.finished.connect(self._on_process_finished)
        self.process.errorOccurred.connect(self._on_process_error)

    def initializePage(self):
        """Called every time the page is shown to set UI state."""
        if self._installation_process_has_finished:
            # Installation is done (succeeded or failed), show logs, disable selection
            self.selection_group_widget.setVisible(False)
            self.log_display_widget.setVisible(True)
            # Buttons are handled by isComplete() -> True, wizard enables Next/Back
        elif self._installation_triggered_for_current_session:
            # Installation has been started but not yet finished
            self.selection_group_widget.setVisible(False)
            self.log_display_widget.setVisible(True)
            if self.process.state() == QProcess.Running:
                 self.wizard().setButtonLayout([QWizard.Stretch, QWizard.CancelButton])
            # If not running, but not finished, it's an odd state (e.g., crash before QProcess.finished)
            # isComplete() will be false, Next click -> validatePage (which should handle this)
        else:
            # Initial state: ready for package selection
            self.selection_group_widget.setVisible(True)
            self.selection_group_widget.setEnabled(True) # Ensure it's enabled
            self.log_display_widget.setVisible(False)
            self.log_text_edit.clear()
            # Reset flags for a potential new run if user navigates back before starting
            self._selected_packages_for_install = []
            self._installation_process_has_finished = False
            self._installation_triggered_for_current_session = False


        self.completeChanged.emit() # Crucial for wizard to update button states

    def isComplete(self) -> bool:
        """Page is complete for navigation only if the installation process has finished."""
        return self._installation_process_has_finished

    def validatePage(self) -> bool:
        """
        Called when 'Next' is clicked and isComplete() is false.
        This method handles the transition from selection to starting the installation.
        """
        if self._installation_triggered_for_current_session:
            # This means installation was started, but isComplete() is false (so not finished).
            # This state implies the process is running or crashed without 'finished' signal.
            # 'Next' button should have been disabled or replaced by 'Cancel'.
            # If user somehow clicks 'Next', prevent proceeding.
            QMessageBox.information(self, "Installation Status", 
                                   "Installation is currently in progress or awaiting completion. Please wait.")
            return False # Stay on page

        # --- Gather selections ---
        current_selections = [opt for opt, cb in self.checkboxes.items() if cb.isChecked()]
        custom_text = self.custom_input_lineedit.text().strip()
        if custom_text:
            current_selections.extend([pkg.strip() for pkg in custom_text.split() if pkg.strip()])

        if not current_selections:
            QMessageBox.warning(self, "No Packages Selected", "Please select packages or enter custom names.")
            return False

        # --- Confirm with user ---
        confirm_msg = (f"You are about to install:\n\n"
                       f"- {', '.join(current_selections)}\n\n"
                       f"This requires administrative privileges (sudo via pkexec).\n"
                       f"Proceed with installation?")
        reply = QMessageBox.question(self, "Confirm Installation", confirm_msg,
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self._selected_packages_for_install = current_selections
            self._start_installation_process()
            return False # Stay on page; installation starts, isComplete() remains false until finished.
        else:
            return False # User cancelled. Stay on page.

    def _start_installation_process(self):
        self._installation_triggered_for_current_session = True
        self._installation_process_has_finished = False # Reset for this run

        self.selection_group_widget.setEnabled(False) # Disable selection UI
        self.selection_group_widget.setVisible(False)
        self.log_display_widget.setVisible(True)
        self.log_text_edit.clear()
        self.log_text_edit.append("Initializing installation...\n")

        # Set wizard buttons to "Cancel" only during installation
        self.wizard().setButtonLayout([QWizard.Stretch, QWizard.CancelButton])
        self.completeChanged.emit() # Ensure wizard reflects non-complete state during install

        # --- Build and run omnipkg script ---
        cmd_mapping = {
            "Education": "sudo /usr/local/bin/omnipkg put install maibloom-edupackage",
            "Programming": "sudo /usr/local/bin/omnipkg put install maibloom-devpackage",
            "Office": "sudo /usr/local/bin/omnipkg put install maibloom-officepackage",
            "Daily Use": "sudo /usr/local/bin/omnipkg put install maibloom-dailypackage",
            "Gaming": "sudo /usr/local/bin/omnipkg put install maibloom-gamingpackage"
        }
        script_parts = []
        if self._selected_packages_for_install:
            for sel in self._selected_packages_for_install:
                safe_sel = "".join(c for c in sel if c.isalnum() or c in ['-', '_', '.']) # Basic sanitization
                if not safe_sel : continue # Skip empty or fully invalid names

                self.log_text_edit.append(f"Queueing: {safe_sel}")
                command = cmd_mapping.get(safe_sel, f"sudo /usr/local/bin/omnipkg put install {safe_sel}")
                
                script_parts.append(f"echo ; echo '> Processing: {safe_sel}...'")
                script_parts.append(command)
                script_parts.append(f"echo '> Finished processing: {safe_sel}.'")
                script_parts.append("sleep 0.2") # Brief pause for visual step
        else:
            script_parts.append("echo ; echo '> No packages were selected for installation.'")
        
        script_parts.append("echo ; echo '== Installation script phase complete. ==' ; echo")
        full_script = "\n".join(script_parts)
        
        self.log_text_edit.append(f"--- Script for pkexec ---\n{full_script}\n-------------------------\n")
        self.process.start("pkexec", ["bash", "-c", full_script])

        if not self.process.waitForStarted(4500): # Increased timeout
            self.log_text_edit.append("<font color='red'>Error: Process failed to start (pkexec timeout or command issue).</font>")
            self._on_process_finished(-1, QProcess.CrashExit, "Process failed to initiate via pkexec.")

    @pyqtSlot()
    def _handle_stdout(self):
        data = self.process.readAllStandardOutput().data().decode(errors='replace').strip()
        if data: self.log_text_edit.append(data)

    @pyqtSlot()
    def _handle_stderr(self):
        data = self.process.readAllStandardError().data().decode(errors='replace').strip()
        if data: self.log_text_edit.append(f"<font color='red'>{data}</font>")

    @pyqtSlot(int, QProcess.ExitStatus)
    def _on_process_finished(self, exit_code=-1, exit_status=QProcess.NormalExit, manual_error_msg=None):
        if self._installation_process_has_finished and not manual_error_msg: # Prevent double-processing if called manually then by signal
            return

        self.log_text_edit.append("\n--- Installation Process Concluded ---")
        if manual_error_msg:
             self.log_text_edit.append(f"<font color='red'>{manual_error_msg}</font>")

        if exit_status == QProcess.NormalExit and exit_code == 0:
            self.log_text_edit.append("<font color='green'>Installation process completed successfully.</font>")
        elif exit_status == QProcess.CrashExit:
            self.log_text_edit.append(f"<font color='red'>Installation process crashed.</font>")
        else:
            self.log_text_edit.append(f"<font color='red'>Installation process finished with errors (code: {exit_code}).</font>")
        
        self._installation_process_has_finished = True
        self.completeChanged.emit() # Key: tell wizard to re-evaluate buttons (Next should enable)

    @pyqtSlot(QProcess.ProcessError)
    def _on_process_error(self, error_enum):
        # This catches QProcess-specific errors (e.g., command not found)
        error_map = {
            QProcess.FailedToStart: "Failed to start", QProcess.Crashed: "Crashed",
            QProcess.Timedout: "Timed out", QProcess.ReadError: "Read error",
            QProcess.WriteError: "Write error", QProcess.UnknownError: "Unknown error"
        }
        process_error_str = self.process.errorString()
        error_msg = error_map.get(error_enum, f"Unspecified QProcess error ({process_error_str})")
        
        # Ensure this also leads to a "finished" state for the page logic
        if not self._installation_process_has_finished: # Only if not already handled by finished signal
             self._on_process_finished(self.process.exitCode() if self.process.exitCode() is not None else -1, 
                                      QProcess.CrashExit, # Treat as a crash for simplicity
                                      f"QProcess Error: {error_msg}")

    def nextId(self) -> int:
        return PageIds.END

# --- End Page ---
class EndPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Setup Complete")
        self.setSubTitle("Press 'Finish' to exit the Mai Bloom setup.")
        
        layout = QVBoxLayout(self)
        lbl = QLabel("Thank you for using the Mai Bloom OS Setup Utility!")
        lbl.setFont(QFont("Arial", 16, QFont.Bold))
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setWordWrap(True)
        layout.addWidget(lbl)

        self.learn_more_button = QPushButton("Learn More (Placeholder)")
        self.learn_more_button.setFont(QFont("Arial", 10))
        self.learn_more_button.clicked.connect(self._show_learn_more)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.learn_more_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        layout.addStretch()
        self.setLayout(layout)

    def _show_learn_more(self):
        QMessageBox.information(self, "Learn More", 
                                "This is a placeholder for information about Mai Bloom, documentation, or next steps.")

    def nextId(self) -> int:
        return -1 # This is the final page

# --- Main Wizard Application ---
class MaiBloomWizard(QWizard):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mai Bloom OS Setup")
        self.setWizardStyle(QWizard.ModernStyle)
        self.setOption(QWizard.NoBackButtonOnStartPage, True)

        self.welcome_page = WelcomePage()
        self.install_select_page = InstallSelectPage() # Keep one instance
        self.end_page = EndPage()

        self.setPage(PageIds.WELCOME, self.welcome_page)
        self.setPage(PageIds.INSTALL_SELECT, self.install_select_page)
        self.setPage(PageIds.END, self.end_page)
        
        self.setStartId(PageIds.WELCOME)
        self.resize(720, 600) # Adjusted size for better layout

    def _handle_installation_cancellation(self, page_instance):
        if page_instance.process and page_instance.process.state() == QProcess.Running:
            page_instance.process.kill()
            page_instance.log_text_edit.append("<font color='orange'>Installation process terminated by user.</font>")
            # Mark as "finished" (though cancelled) so UI doesn't get stuck
            if not page_instance._installation_process_has_finished:
                 page_instance._on_process_finished(-1, QProcess.CrashExit, "Installation cancelled by user action.")


    def closeEvent(self, event):
        if self.currentId() == PageIds.INSTALL_SELECT:
            if self.install_select_page.process.state() == QProcess.Running:
                reply = QMessageBox.question(self, "Confirm Exit",
                                           "Installation is in progress. Exit now?",
                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.No:
                    event.ignore()
                    return
                else:
                    self._handle_installation_cancellation(self.install_select_page)
        event.accept()

    def done(self, result):
        if result == QDialog.Rejected and self.currentId() == PageIds.INSTALL_SELECT:
             self._handle_installation_cancellation(self.install_select_page)
        super().done(result)

# --- Main Execution ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    wizard = MaiBloomWizard()
    wizard.show()
    sys.exit(app.exec_())

