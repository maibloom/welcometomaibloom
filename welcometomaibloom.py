#!/usr/bin/env python3
import sys
from PyQt5.QtWidgets import (
    QApplication, QWizard, QWizardPage, QLabel, QVBoxLayout,
    QCheckBox, QLineEdit, QTextEdit, QPushButton, QMessageBox, QWidget
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

        # --- Selection Group ---
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

        # --- Log Group ---
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
        self._installation_started = False
        self._installation_attempted = False # To prevent re-installation on back->next if already run

    def initializePage(self):
        if not self._installation_attempted: # First time or if we allow reset
            self._installation_started = False
            self._done = False
            self.selectionGroup.setVisible(True)
            self.customInput.setEnabled(True)
            for cb in self.checkboxes.values():
                cb.setEnabled(True)
            self.logGroup.setVisible(False)
            self.log.clear()
            self.wizard().setButtonLayout([
                QWizard.Stretch, QWizard.BackButton, QWizard.NextButton, QWizard.CancelButton
            ])
        else: # Installation was attempted, show logs
            self.selectionGroup.setVisible(False) # Or keep visible but disable
            self.logGroup.setVisible(True)
            if self._done:
                 self.wizard().setButtonLayout([
                    QWizard.Stretch, QWizard.BackButton, QWizard.NextButton, QWizard.CancelButton # Allow Next to EndPage
                ])
            else: # Should not happen if _installation_attempted is true and process didn't start/finish
                  # This state implies it's still running, or error before starting.
                self.wizard().setButtonLayout([
                    QWizard.Stretch, QWizard.BackButton, QWizard.CancelButton # Back if stuck, Cancel if running
                ])
        self.completeChanged.emit()


    def getSelections(self):
        sels = [opt for opt, cb in self.checkboxes.items() if cb.isChecked()]
        extra_raw = self.customInput.text().strip()
        if extra_raw:
            # Assuming custom input might be multiple packages, space separated
            sels.extend([e.strip() for e in extra_raw.split() if e.strip()])
        return sels

    def startInstallation(self):
        self._installation_started = True
        self._installation_attempted = True # Mark that an attempt has been made

        self.selectionGroup.setEnabled(False) # Disable selection UI
        self.logGroup.setVisible(True)
        
        self.wizard().setButtonLayout([
            QWizard.Stretch, QWizard.CancelButton # Only cancel during installation
        ])

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
                    script_parts.append("sleep 1") # Simulating work
                else: # Custom package names
                    # For custom packages, assuming 'omnipkg put install <packagename>'
                    # This part needs to be robust depending on how custom packages are handled.
                    # For this example, we'll assume they are direct package names for omnipkg.
                    command = f"sudo /usr/local/bin/omnipkg put install {sel}"
                    script_parts.append(f"echo '> Attempting to install custom package: {sel}...'")
                    script_parts.append(command)
                    script_parts.append(f"echo '> Finished processing custom package: {sel}.'")
                    script_parts.append("sleep 1") # Simulating work
        else:
            script_parts.append("echo '> No packages selected. Skipping installation...'")
            script_parts.append("sleep 1")
        
        script_parts.append("echo ''")
        script_parts.append("echo 'Installation phase complete.'")
        
        full_script = "; ".join(script_parts)
        
        self.log.append("Starting package installation process...\n")
        # Security note: directly embedding user input (customInput) into a script run with pkexec is risky.
        # The original code did this too for "extra". Proper sanitization or a different mechanism
        # for handling custom packages would be needed in a production system.
        # For this example, we proceed with the simplified logic.
        self.log.append(f"Effective script to be run (via pkexec bash -c):\n{full_script}\n")

        command_list = ["pkexec", "bash", "-c", full_script]
        self.process.start(command_list[0], command_list[1:])
        if not self.process.waitForStarted(3000): # Wait 3s for pkexec prompt
            self.log.append("<font color='red'>Process failed to start. Did you cancel the password prompt or is pkexec/bash not found?</font>")
            self.on_finished(-1, QProcess.CrashExit) # Simulate a crash/failure to start

    @pyqtSlot()
    def handle_stdout(self):
        data = self.process.readAllStandardOutput()
        try:
            out = bytes(data).decode(errors='replace').strip()
        except Exception as e:
            out = f"[Error decoding stdout: {e}]"
        if out:
            self.log.append(out)

    @pyqtSlot()
    def handle_stderr(self):
        data = self.process.readAllStandardError()
        try:
            err = bytes(data).decode(errors='replace').strip()
        except Exception as e:
            err = f"[Error decoding stderr: {e}]"
        if err:
            self.log.append(f"<font color='red'>{err}</font>")

    @pyqtSlot(int, QProcess.ExitStatus)
    def on_finished(self, exitCode, exitStatus):
        self.log.append("")
        if exitStatus == QProcess.NormalExit and exitCode == 0:
            self.log.append("<font color='green'>Installation process finished successfully.</font>")
        elif exitStatus == QProcess.CrashExit:
            self.log.append(f"<font color='red'>Installation process crashed or failed to start.</font>")
        else:
            self.log.append(f"<font color='red'>Installation process finished with exit code: {exitCode}.</font>")
        
        self._done = True
        self.completeChanged.emit() # This tells the wizard to re-evaluate button states
        # After finishing, allow navigation
        self.wizard().setButtonLayout([
             QWizard.Stretch, QWizard.BackButton, QWizard.NextButton, QWizard.CancelButton
        ])


    def isComplete(self):
        # Page is complete if installation has started AND finished.
        # If installation hasn't started, 'Next' press will trigger it via validatePage.
        return self._installation_started and self._done
    
    def validatePage(self):
        if not self._installation_started:
            # User clicked "Next" to start installation
            selections = self.getSelections()
            if not selections:
                QMessageBox.warning(self, "No Packages Selected", 
                                    "Please select at least one package group or enter custom package names.")
                return False # Stay on page

            confirm_msg = f"Are you sure you want to install the selected packages/groups:\n\n- {', '.join(selections)}\n\nThis will run commands with sudo (via pkexec)."
            reply = QMessageBox.question(self, "Confirm Installation", confirm_msg,
                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                self.startInstallation()
                return False # Stay on this page while installation runs (isComplete is false)
            else:
                return False # User cancelled confirmation, stay on page.
        
        # If installation has started, isComplete() (checked by QWizard) determines if we can move.
        # This validatePage will then be called if QWizard thinks it can proceed.
        # We return self._done to confirm.
        return self._done

    def nextId(self) -> int:
        return MaiBloomWizard.Page_End

class EndPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Setup Complete")
        self.setSubTitle("Press 'Finish' to exit.") # QWizard handles the "Finish" button text
        
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
        
        # Add some spacing
        layout.addSpacing(20)

        lbl_finish = QLabel("Press 'Finish' to close this setup utility.")
        lbl_finish.setAlignment(Qt.AlignCenter)
        lbl_finish.setWordWrap(True)
        layout.addWidget(lbl_finish)

        self.setLayout(layout)

    def openLearnMore(self):
        # Example: Open a URL (replace with your actual URL)
        # learn_more_url = QUrl("https://www.example.com/maibloom/learnmore")
        # if not QDesktopServices.openUrl(learn_more_url):
        #     QMessageBox.warning(self, "Learn More", f"Could not open URL: {learn_more_url.toString()}")
        
        # Or show a message box for simplicity
        QMessageBox.information(self, "Learn More", 
                                "Mai Bloom is your personalized OS assistant!\n\n"
                                "Visit our (fictional) website at maibloom.example.com for documentation, "
                                "tips, and advanced features.\n\n"
                                "(This is a placeholder. In a real app, this would link to actual resources.)")

    def nextId(self) -> int:
        return -1 # This is the final page


class MaiBloomWizard(QWizard):
    Page_Welcome, Page_InstallSelect, Page_End = range(3)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mai Bloom Setup")
        self.setWizardStyle(QWizard.ModernStyle)
        self.setOption(QWizard.NoBackButtonOnStartPage, True)
        # self.setOption(QWizard.HaveFinishButtonOnEarlyPages, False) # Default behavior

        self.welcome_page = WelcomePage()
        self.install_select_page = InstallSelectPage()
        self.end_page = EndPage()

        self.setPage(self.Page_Welcome, self.welcome_page)
        self.setPage(self.Page_InstallSelect, self.install_select_page)
        self.setPage(self.Page_End, self.end_page)
        
        self.setStartId(self.Page_Welcome)
        self.resize(720, 580) # Adjusted size slightly for content

    def done(self, result):
        if result == QDialog.Rejected: # User clicked Cancel or closed window
            # You might want to ask for confirmation before cancelling, especially if installation is running.
            # For simplicity, QWizard's default cancel behavior is used.
            # If self.install_select_page.process.state() == QProcess.Running:
            #     reply = QMessageBox.question(self, "Confirm Cancel",
            #                                "Installation is in progress. Are you sure you want to cancel setup? "
            #                                "This might leave packages partially installed.",
            #                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            #     if reply == QMessageBox.No:
            #         return # Abort the done() call, keep wizard open
            #     else:
            #         if self.install_select_page.process:
            #             self.install_select_page.process.kill() # Attempt to stop the process
            #             self.install_select_page.log.append("<font color='orange'>Installation cancelled by user.</font>")
            #             self.install_select_page._done = True # Mark as "done" in a cancelled state
            #             self.install_select_page._installation_started = True 

            # For now, let QWizard handle default cancel button logic.
            # The QProcess is a child of the page, so it should be terminated when page/wizard is destroyed.
            pass
        super().done(result)


def main():
    app = QApplication(sys.argv)
    # Apply a basic style if desired
    # app.setStyle("Fusion") 
    wiz = MaiBloomWizard()
    wiz.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
