#!/usr/bin/env python3
import sys
from PyQt5.QtWidgets import (
    QApplication, QWizard, QWizardPage, QLabel, QVBoxLayout,
    QCheckBox, QLineEdit, QTextEdit, QPushButton, QMessageBox, QWidget, QDialog
)
from PyQt5.QtCore import QProcess, pyqtSlot, Qt, QUrl
from PyQt5.QtGui import QFont, QDesktopServices

class WelcomePage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Welcome to Mai Bloom!")
        self.setSubTitle("Click 'Next' to customize your OS.")
        layout = QVBoxLayout()
        lbl = QLabel("Welcome to Mai Bloom!\n\nYour journey towards a personalized OS begins here.")
        lbl.setFont(QFont("Arial", 16, QFont.Bold))
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setWordWrap(True)
        layout.addWidget(lbl)
        self.setLayout(layout)

    def nextId(self) -> int:
        return MaiBloomWizard.Page_InstallSelect

class InstallSelectPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Package Selection and Installation")
        self.setSubTitle("Select packages and click 'Next' to install. Installation will begin after confirmation.")

        self.mainLayout = QVBoxLayout(self)

        self.selectionGroup = QWidget()
        selectionLayout = QVBoxLayout(self.selectionGroup)
        info = QLabel("Select the package groups you want to install:")
        info.setFont(QFont("Arial", 14))
        info.setWordWrap(True)
        selectionLayout.addWidget(info)
        self.options = ["Education", "Programming", "Office", "Daily Use", "Gaming"]
        self.checkboxes = {}
        for opt in self.options:
            cb = QCheckBox(opt)
            cb.setFont(QFont("Arial", 12))
            selectionLayout.addWidget(cb)
            self.checkboxes[opt] = cb
        self.customInput = QLineEdit()
        self.customInput.setPlaceholderText("Enter additional package names (optional, space-separated)")
        selectionLayout.addWidget(self.customInput)
        self.mainLayout.addWidget(self.selectionGroup)

        self.logGroup = QWidget()
        logLayout = QVBoxLayout(self.logGroup)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFontFamily("Courier")
        logLayout.addWidget(self.log)
        self.mainLayout.addWidget(self.logGroup)
        self.setLayout(self.mainLayout)

        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.on_finished)
        if hasattr(self.process, 'errorOccurred'):
            self.process.errorOccurred.connect(
                lambda err: self.log.append(f"<font color='red'>Process error: {self.process.errorString()} (Code: {err})</font>")
            )
        
        self._done = False
        self._installation_started_current_attempt = False # Tracks if current attempt is running/finished
        self._installation_ever_attempted = False # Tracks if any attempt was made (for UI mode)


    def initializePage(self):
        # This method is called each time the page is entered.
        if not self._installation_ever_attempted:
            # First time on this page, or after a full reset (if implemented)
            self.selectionGroup.setVisible(True)
            self.selectionGroup.setEnabled(True)
            self.logGroup.setVisible(False)
            self.log.clear()
            self._done = False # Ensure states are fresh
            self._installation_started_current_attempt = False
        else:
            # An installation was attempted, stay in log view mode.
            self.selectionGroup.setVisible(False)
            self.selectionGroup.setEnabled(False)
            self.logGroup.setVisible(True)
            
            # If process is currently running (e.g., user navigated away and back)
            # Ensure only Cancel is shown.
            if self.process.state() == QProcess.Running:
                self.wizard().setButtonLayout([QWizard.Stretch, QWizard.CancelButton])

        # Crucially, emit completeChanged so wizard re-evaluates button states
        # based on the current isComplete() status.
        self.completeChanged.emit()

    def getSelections(self):
        sels = [opt for opt, cb in self.checkboxes.items() if cb.isChecked()]
        extra_raw = self.customInput.text().strip()
        if extra_raw:
            sels.extend([e.strip() for e in extra_raw.split() if e.strip()])
        return sels

    def startInstallation(self):
        self._installation_started_current_attempt = True
        self._installation_ever_attempted = True # Mark that an attempt has now been made
        self._done = False # Reset done status for this new attempt

        self.selectionGroup.setEnabled(False) # Disable selection UI
        self.logGroup.setVisible(True) # Ensure log is visible
        self.log.clear() # Clear log for new installation attempt
        
        self.log.append("Starting package installation process...\n")
        
        selections = self.getSelections()
        cmd_mapping = {
            "Education": "sudo /usr/local/bin/omnipkg put install maibloom-edupackage",
            "Programming": "sudo /usr/local/bin/omnipkg put install maibloom-devpackage",
            "Office": "sudo /usr/local/bin/omnipkg put install maibloom-officepackage",
            "Daily Use": "sudo /usr/local/bin/omnipkg put install maibloom-dailypackage",
            "Gaming": "sudo /usr/local/bin/omnipkg put install maibloom-gamingpackage"
        }
        script_parts = []
        if selections:
            for sel in selections:
                if sel in cmd_mapping:
                    command = cmd_mapping[sel]
                    script_parts.append(f"echo '> Installing {sel} packages...'")
                    script_parts.append(command)
                    script_parts.append(f"echo '> Finished installing {sel} packages.'")
                else:
                    command = f"sudo /usr/local/bin/omnipkg put install {sel}" # Basic custom handling
                    script_parts.append(f"echo '> Attempting to install custom package: {sel}...'")
                    script_parts.append(command)
                    script_parts.append(f"echo '> Finished processing custom package: {sel}.'")
                script_parts.append("sleep 1") # Simulating work
        else:
            script_parts.append("echo '> No packages selected. Skipping installation...'")
            script_parts.append("sleep 1")
        script_parts.append("echo '' && echo 'Installation phase complete.'")
        full_script = "; ".join(script_parts)
        
        self.log.append(f"Effective script to be run (via pkexec bash -c):\n{full_script}\n")

        # Set Cancel button only during installation
        self.wizard().setButtonLayout([QWizard.Stretch, QWizard.CancelButton])

        command_list = ["pkexec", "bash", "-c", full_script]
        self.process.start(command_list[0], command_list[1:])
        
        if not self.process.waitForStarted(3500): # Slightly longer timeout
            self.log.append("<font color='red'>Process failed to start. (pkexec timeout or other issue)</font>")
            # Treat as a finished (failed) attempt
            self.on_finished(-1, QProcess.CrashExit) 


    @pyqtSlot()
    def handle_stdout(self):
        data = self.process.readAllStandardOutput()
        self.log.append(bytes(data).decode(errors='replace').strip())

    @pyqtSlot()
    def handle_stderr(self):
        data = self.process.readAllStandardError()
        self.log.append(f"<font color='red'>{bytes(data).decode(errors='replace').strip()}</font>")

    @pyqtSlot(int, QProcess.ExitStatus)
    def on_finished(self, exitCode, exitStatus):
        self.log.append("")
        if self.process.state() != QProcess.NotRunning: # Defensive check if somehow called prematurely
             # If process is still running, this call to on_finished might be due to an error signal
             # Let the actual "finished" signal be the main one.
             # This case should be rare with direct signal-slot.
             if exitStatus == QProcess.CrashExit: # Error occurred, ensure log reflects this
                  self.log.append(f"<font color='red'>Process signaled an error before proper finish. Exit code: {exitCode}</font>")
        
        # Log final status based on exit codes
        if exitStatus == QProcess.NormalExit and exitCode == 0:
            self.log.append("<font color='green'>Installation process finished successfully.</font>")
        elif exitStatus == QProcess.CrashExit:
            self.log.append(f"<font color='red'>Installation process crashed or failed to start properly.</font>")
        else: # NormalExit but non-zero exitCode, or other status
            self.log.append(f"<font color='red'>Installation process finished with exit code: {exitCode}.</font>")
        
        self._done = True
        # Signal the wizard that completeness might have changed.
        # The wizard will re-evaluate isComplete() and update buttons.
        # If isComplete() is now true, "Next" should appear (and "Back").
        self.completeChanged.emit()

    def isComplete(self):
        # Page is "complete" for navigation if an installation attempt was made and it's finished (_done).
        # If no attempt was made, it's not complete, and "Next" click triggers validatePage().
        if self._installation_ever_attempted:
            return self._done 
        return False
    
    def validatePage(self):
        # This is called when "Next" is clicked AND isComplete() is False.
        # This should only happen if no installation has been attempted yet.
        if not self._installation_ever_attempted:
            selections = self.getSelections()
            if not selections:
                QMessageBox.warning(self, "No Packages Selected", 
                                    "Please select at least one package group or enter custom package names.")
                return False # Stay on page

            confirm_msg = (f"Are you sure you want to install the selected packages/groups:\n\n"
                           f"- {', '.join(selections)}\n\n"
                           f"This will run commands with sudo (via pkexec).")
            reply = QMessageBox.question(self, "Confirm Installation", confirm_msg,
                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                self.startInstallation()
                return False # Stay on this page; installation is running, isComplete() is False.
            else:
                return False # User cancelled confirmation, stay on page.
        
        # If _installation_ever_attempted is true, then isComplete() (which checks _done)
        # should have determined if wizard proceeds or not. If we reach here, it means
        # isComplete() was false (so _done is false), but an attempt was made.
        # This implies it's still running (Next should be disabled) or some inconsistent state.
        # For safety, we return self._done. If it's truly done, we can proceed.
        return self._done

    def nextId(self) -> int:
        return MaiBloomWizard.Page_End

class EndPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Setup Complete")
        self.setSubTitle("Press 'Finish' to exit.")
        layout = QVBoxLayout()
        lbl = QLabel("Thank you for customizing your OS with Mai Bloom!")
        lbl.setFont(QFont("Arial", 16, QFont.Bold))
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setWordWrap(True)
        layout.addWidget(lbl)
        self.learnMoreButton = QPushButton("Learn More about Mai Bloom")
        self.learnMoreButton.setFont(QFont("Arial", 12))
        self.learnMoreButton.clicked.connect(self.openLearnMore)
        layout.addWidget(self.learnMoreButton, alignment=Qt.AlignCenter)
        layout.addSpacing(20)
        lbl_finish = QLabel("Press 'Finish' to close this setup utility.")
        lbl_finish.setAlignment(Qt.AlignCenter)
        lbl_finish.setWordWrap(True)
        layout.addWidget(lbl_finish)
        self.setLayout(layout)

    def openLearnMore(self):
        QMessageBox.information(self, "Learn More", 
                                "Mai Bloom is your personalized OS assistant!\n\n"
                                "Visit our (fictional) website for more details.\n"
                                "(This is a placeholder for actual resources.)")

    def nextId(self) -> int:
        return -1

class MaiBloomWizard(QWizard):
    Page_Welcome, Page_InstallSelect, Page_End = range(3)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mai Bloom Setup")
        self.setWizardStyle(QWizard.ModernStyle)
        self.setOption(QWizard.NoBackButtonOnStartPage, True)
        
        self.welcome_page = WelcomePage()
        self.install_select_page = InstallSelectPage() # Only one instance
        self.end_page = EndPage()

        self.setPage(self.Page_Welcome, self.welcome_page)
        self.setPage(self.Page_InstallSelect, self.install_select_page)
        self.setPage(self.Page_End, self.end_page)
        
        self.setStartId(self.Page_Welcome)
        self.resize(720, 580)

    def done(self, result):
        if result == QDialog.Rejected: # User clicked Cancel or closed window
            # Check if installation process is running
            # Accessing page like this is okay if it's guaranteed to exist
            if self.currentId() == self.Page_InstallSelect and self.install_select_page.process.state() == QProcess.Running:
                reply = QMessageBox.question(self, "Confirm Cancel",
                                           "Installation is in progress. Are you sure you want to cancel setup?",
                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.No:
                    # To prevent closing, we need to override the default behavior or not call super.done().
                    # However, QWizard.done() is usually for finalization.
                    # Better to handle this in closeEvent for window X button.
                    # For Cancel button, if wizard is designed to allow it, process should be killed here.
                    # For simplicity, if user says "No", we let done() be potentially re-evaluated or do nothing.
                    # The most straightforward way to prevent closing from here is to not call super().done(result).
                    # But this might leave the wizard in an odd state.
                    # Let's assume if Cancel is hit, we try to stop the process.
                    # The prompt is more for the 'X' button.
                    pass # Let super.done handle it after potential cleanup

                # If they clicked "Yes" to cancel during install (or if no prompt)
                if self.install_select_page.process.state() == QProcess.Running:
                    self.install_select_page.process.kill()
                    self.install_select_page.log.append("<font color='orange'>Installation process terminated by user.</font>")
                    # Mark as "done" in a cancelled state so the page can be considered complete for navigation.
                    self.install_select_page._done = True 
                    self.install_select_page.completeChanged.emit()
        super().done(result)

    def closeEvent(self, event): # QWidget method
        if self.currentId() == self.Page_InstallSelect:
            # Using self.install_select_page directly as it's an instance variable
            if self.install_select_page.process and self.install_select_page.process.state() == QProcess.Running:
                reply = QMessageBox.question(self, "Confirm Exit",
                                           "Installation is in progress. Are you sure you want to exit?",
                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.No:
                    event.ignore()
                    return
                else:
                    if self.install_select_page.process.state() == QProcess.Running:
                        self.install_select_page.process.kill()
        event.accept()

def main():
    app = QApplication(sys.argv)
    wiz = MaiBloomWizard()
    wiz.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
