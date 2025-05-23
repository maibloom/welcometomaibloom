import sys
from PyQt5.QtWidgets import (
    QApplication, QWizard, QWizardPage, QLabel, QVBoxLayout,
    QCheckBox, QLineEdit, QTextEdit, QPushButton, QMessageBox
)
from PyQt5.QtCore import QProcess, pyqtSlot, Qt
from PyQt5.QtGui import QFont

# Page 1: Welcome Page
class WelcomePage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Welcome to Mai Bloom!")
        self.setSubTitle("Tab 'Next' to customize your OS.")
        layout = QVBoxLayout()
        label = QLabel("Welcome to Mai Bloom!\n\nYour journey towards a personalized OS begins here.")
        label.setFont(QFont("Arial", 16, QFont.Bold))
        label.setAlignment(Qt.AlignCenter)
        label.setWordWrap(True)
        layout.addWidget(label)
        self.setLayout(layout)

# Page 2: Purpose/Customization Page
class PurposePage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Customize Your OS")
        self.setSubTitle("For which purpose do you use your computer?")
        layout = QVBoxLayout()
        info_label = QLabel("Select the package groups you want to install:")
        info_label.setFont(QFont("Arial", 14))
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Define several checkboxes with common OS-purpose options.
        self.options = ["Education", "Programming", "Office", "Daily Use", "Gaming"]
        self.checkboxes = {}
        for option in self.options:
            cb = QCheckBox(option)
            cb.setFont(QFont("Arial", 12))
            self.checkboxes[option] = cb
            layout.addWidget(cb)

        # Allow user to enter an additional purpose, if desired.
        self.customInput = QLineEdit()
        self.customInput.setPlaceholderText("Enter additional purpose (optional)")
        layout.addWidget(self.customInput)

        self.setLayout(layout)

    def getSelections(self):
        selections = []
        for option, cb in self.checkboxes.items():
            if cb.isChecked():
                selections.append(option)
        additional = self.customInput.text().strip()
        if additional:
            selections.append(additional)
        return selections

# Page 3: Installation Page
class InstallationPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Installing Selected Packages")
        self.setSubTitle("Please wait while your packages are installed...")
        layout = QVBoxLayout()
        self.textEdit = QTextEdit()
        self.textEdit.setReadOnly(True)
        self.textEdit.setFontFamily("Courier")
        layout.addWidget(self.textEdit)
        self.setLayout(layout)

        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.installationFinished)
        self.installation_done = False

    def initializePage(self):
        # Clear previous text and reset installation state.
        self.textEdit.clear()
        self.installation_done = False
        # Retrieve user selections from the PurposePage.
        purpose_page = self.wizard().page(1)
        selections = purpose_page.getSelections()
        if selections:
            # Build a command that simulates installation output for each selection.
            # (In a real scenario, you would run actual installation commands.)
            cmd = "bash"
            script = ""
            for sel in selections:
                script += f"echo 'Installing {sel} packages...'; sleep 1;"
            script += "echo 'Installation complete.'"
        else:
            cmd = "bash"
            script = "echo 'No packages selected. Skipping installation...'; sleep 1; echo 'Installation complete.'"

        # Start the QProcess with the constructed bash command.
        self.process.start(cmd, ["-c", script])

    @pyqtSlot()
    def handle_stdout(self):
        data = self.process.readAllStandardOutput().data().decode()
        self.textEdit.append(data)

    @pyqtSlot()
    def handle_stderr(self):
        data = self.process.readAllStandardError().data().decode()
        self.textEdit.append(f"<font color='red'>{data}</font>")

    @pyqtSlot()
    def installationFinished(self):
        self.textEdit.append("\n<font color='green'>Installation process finished.</font>")
        self.installation_done = True
        self.completeChanged.emit()

    def isComplete(self):
        return self.installation_done

# Page 4: App Introduction Page
class AppIntroductionPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Introducing X App")
        self.setSubTitle("Discover and launch the X App, your new productivity assistant!")
        layout = QVBoxLayout()
        description = QLabel("X App is designed to enhance your workflow and productivity.\n"
                             "Click the button below to launch the application.")
        description.setWordWrap(True)
        description.setFont(QFont("Arial", 14))
        layout.addWidget(description)
        self.openButton = QPushButton("Open X App")
        self.openButton.setFont(QFont("Arial", 12))
        self.openButton.clicked.connect(self.openApp)
        layout.addWidget(self.openButton, alignment=Qt.AlignCenter)
        self.setLayout(layout)

    def openApp(self):
        # For demonstration, show a message. In a real scenario, launch the desired application.
        QMessageBox.information(self, "X App", "X App has been launched!")
        # Example: QProcess.startDetached("xterm", ["-e", "your_app_command"])

# Page 5: Final Page
class FinalPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Finish")
        layout = QVBoxLayout()
        label = QLabel("Thank you for customizing your OS with Mai Bloom!\nPress 'Finish' to exit.")
        label.setWordWrap(True)
        label.setFont(QFont("Arial", 16, QFont.Bold))
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        self.setLayout(layout)

def main():
    app = QApplication(sys.argv)
    wizard = QWizard()
    wizard.setWindowTitle("Mai Bloom Welcome App")
    wizard.setWizardStyle(QWizard.ModernStyle)
    wizard.setOption(QWizard.NoBackButtonOnStartPage, True)
    
    # Add the pages in sequential order.
    wizard.addPage(WelcomePage())
    wizard.addPage(PurposePage())
    wizard.addPage(InstallationPage())
    wizard.addPage(AppIntroductionPage())
    wizard.addPage(FinalPage())
    
    wizard.resize(600, 400)
    wizard.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
