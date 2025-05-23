#!/usr/bin/env python3
import sys
from PyQt5.QtWidgets import (
    QApplication, QWizard, QWizardPage, QLabel, QVBoxLayout,
    QCheckBox, QLineEdit, QTextEdit, QPushButton, QMessageBox
)
from PyQt5.QtCore import QProcess, pyqtSlot, Qt
from PyQt5.QtGui import QFont

# Page 1: Welcome
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


# Page 2: Purpose / Customization
class PurposePage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Customize Your OS")
        self.setSubTitle("For which purpose do you use your computer?")
        layout = QVBoxLayout()

        info = QLabel("Select the package groups you want to install:")
        info.setFont(QFont("Arial", 14))
        info.setWordWrap(True)
        layout.addWidget(info)

        self.options = ["Education", "Programming", "Office", "Daily Use", "Gaming"]
        self.checkboxes = {}
        for opt in self.options:
            cb = QCheckBox(opt)
            cb.setFont(QFont("Arial", 12))
            layout.addWidget(cb)
            self.checkboxes[opt] = cb

        self.customInput = QLineEdit()
        self.customInput.setPlaceholderText("Enter additional purpose (optional)")
        layout.addWidget(self.customInput)

        self.setLayout(layout)

    def getSelections(self):
        sels = [opt for opt, cb in self.checkboxes.items() if cb.isChecked()]
        extra = self.customInput.text().strip()
        if extra:
            sels.append(extra)
        return sels


# Page 3: Installation
class InstallationPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Installing Selected Packages")
        self.setSubTitle("Please wait while your packages are installed...")
        layout = QVBoxLayout()
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFontFamily("Courier")
        layout.addWidget(self.log)
        self.setLayout(layout)

        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.on_finished)
        # new: error logging
        if hasattr(self.process, 'errorOccurred'):
            self.process.errorOccurred.connect(
                lambda err: self.log.append(f"<font color='red'>Process error: {err}</font>")
            )
        self._done = False

    def initializePage(self):
        self.log.clear()
        self._done = False
        # safely grab the PurposePage instance
        pp = getattr(self.wizard(), 'purpose_page', None)
        if isinstance(pp, PurposePage):
            selections = pp.getSelections()
        else:
            selections = []

        script = ""
        if selections:
            for sel in selections:
                script += f"echo 'Installing {sel} packages...'; sleep 1; "
        else:
            script = "echo 'No packages selected. Skipping installation...'; sleep 1; "
        script += "echo 'Installation complete.'"

        self.process.start("bash", ["-lc", script])

    @pyqtSlot()
    def handle_stdout(self):
        out = bytes(self.process.readAllStandardOutput()).decode()
        self.log.append(out)

    @pyqtSlot()
    def handle_stderr(self):
        err = bytes(self.process.readAllStandardError()).decode()
        self.log.append(f"<font color='red'>{err}</font>")

    @pyqtSlot()
    def on_finished(self):
        self.log.append("<br><font color='green'>Installation process finished.</font>")
        self._done = True
        self.completeChanged.emit()

    def isComplete(self):
        return self._done


# Page 4: App Intro
class AppIntroductionPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Introducing X App")
        self.setSubTitle("Discover and launch the X App, your new productivity assistant!")
        layout = QVBoxLayout()
        desc = QLabel(
            "X App is designed to enhance your workflow and productivity.\n"
            "Click the button below to launch the application."
        )
        desc.setWordWrap(True)
        desc.setFont(QFont("Arial", 14))
        layout.addWidget(desc)

        self.btn = QPushButton("Open X App")
        self.btn.setFont(QFont("Arial", 12))
        self.btn.clicked.connect(self.openApp)
        layout.addWidget(self.btn, alignment=Qt.AlignCenter)

        self.setLayout(layout)

    def openApp(self):
        # replace with your actual command
        QProcess.startDetached("gedit")
        QMessageBox.information(self, "X App", "X App has been launched!")


# Page 5: Final
class FinalPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Finish")
        layout = QVBoxLayout()
        lbl = QLabel("Thank you for customizing your OS with Mai Bloom!\nPress 'Finish' to exit.")
        lbl.setWordWrap(True)
        lbl.setFont(QFont("Arial", 16, QFont.Bold))
        lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl)
        self.setLayout(layout)


def main():
    app = QApplication(sys.argv)
    wiz = QWizard()
    wiz.setWindowTitle("Mai Bloom Welcome App")
    wiz.setWizardStyle(QWizard.ModernStyle)
    wiz.setOption(QWizard.NoBackButtonOnStartPage, True)

    # create and keep references to pages
    wiz.welcome_page = WelcomePage()
    wiz.purpose_page = PurposePage()
    wiz.install_page = InstallationPage()
    wiz.intro_page = AppIntroductionPage()
    wiz.final_page = FinalPage()

    # add them in order
    wiz.addPage(wiz.welcome_page)
    wiz.addPage(wiz.purpose_page)
    wiz.addPage(wiz.install_page)
    wiz.addPage(wiz.intro_page)
    wiz.addPage(wiz.final_page)

    wiz.resize(600, 400)
    wiz.show()
    sys.exit(app.exec_())


main()