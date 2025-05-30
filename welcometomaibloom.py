#!/usr/bin/env python3
import sys
from PyQt5.QtWidgets import (
    QApplication, QWizard, QWizardPage, QLabel, QVBoxLayout,
    QCheckBox, QLineEdit, QTextEdit, QPushButton, QMessageBox
)
from PyQt5.QtCore import QProcess, pyqtSlot, Qt
from PyQt5.QtGui import QFont

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
        if hasattr(self.process, 'errorOccurred'):
            self.process.errorOccurred.connect(
                lambda err: self.log.append(f"<font color='red'>Process error: {self.process.errorString()} (Code: {err})</font>")
            )
        self._done = False

    def initializePage(self):
        self.log.clear()
        self._done = False
        self.wizard().setButtonLayout([
            QWizard.Stretch, QWizard.CancelButton
        ])


        pp = getattr(self.wizard(), 'purpose_page', None)
        selections = pp.getSelections() if isinstance(pp, PurposePage) else []

        cmd_mapping = {
            "Education": "omnipkg put install maibloom-edupackage",
            "Programming": "omnipkg put install maibloom-devpackage",
            "Office": "omnipkg put install maibloom-officepackage",
            "Daily Use": "omnipkg put install maibloom-dailypackage",
            "Gaming": "omnipkg put install maibloom-gamingpackage"
        }

        script_parts = []
        if selections:
            for sel in selections:
                if sel in cmd_mapping:
                    command = cmd_mapping[sel]
                    script_parts.append(f"echo '> Installing {sel} packages...'")
                    script_parts.append(command)
                    script_parts.append(f"echo '> Finished installing {sel} packages.'")
                    script_parts.append("sleep 1")
                else:
                    script_parts.append(f"echo '> No installation command defined for \"{sel}\". Skipping.'")
                    script_parts.append("sleep 1")
        else:
            script_parts.append("echo '> No packages selected. Skipping installation...'")
            script_parts.append("sleep 1")
        
        script_parts.append("echo ''")
        script_parts.append("echo 'Installation phase complete.'")
        
        full_script = "; ".join(script_parts)
        
        self.log.append("Starting package installation process...\n")
        self.log.append(f"Effective script to be run via pkexec bash -c \"{full_script}\"\n")


        command_list = ["pkexec", "bash", "-c", full_script]
        self.process.start(command_list[0], command_list[1:])


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
            self.log.append(f"<font color='red'>Installation process crashed.</font>")
        else:
            self.log.append(f"<font color='red'>Installation process finished with exit code: {exitCode}.</font>")
        
        self._done = True
        self.completeChanged.emit()
        self.wizard().setButtonLayout([
            QWizard.Stretch, QWizard.BackButton, QWizard.NextButton, QWizard.FinishButton, QWizard.CancelButton
        ])


    def isComplete(self):
        return self._done
    
    def nextId(self) -> int:
        return MaiBloomWizard.Page_Intro


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
        QProcess.startDetached("gedit", [])
        QMessageBox.information(self, "X App", "X App has been launched!")
    
    def nextId(self) -> int:
        return MaiBloomWizard.Page_Final

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

    def nextId(self) -> int:
        return -1


class MaiBloomWizard(QWizard):
    Page_Welcome, Page_Purpose, Page_Install, Page_Intro, Page_Final = range(5)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mai Bloom Welcome App")
        self.setWizardStyle(QWizard.ModernStyle)
        self.setOption(QWizard.NoBackButtonOnStartPage, True)

        self.welcome_page = WelcomePage()
        self.purpose_page = PurposePage()
        self.install_page = InstallationPage()
        self.intro_page = AppIntroductionPage()
        self.final_page = FinalPage()

        self.setPage(self.Page_Welcome, self.welcome_page)
        self.setPage(self.Page_Purpose, self.purpose_page)
        self.setPage(self.Page_Install, self.install_page)
        self.setPage(self.Page_Intro, self.intro_page)
        self.setPage(self.Page_Final, self.final_page)
        
        self.setStartId(self.Page_Welcome)
        self.resize(700, 500)


def main():
    app = QApplication(sys.argv)
    wiz = MaiBloomWizard()
    wiz.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
