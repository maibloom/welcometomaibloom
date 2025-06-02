import sys
import webbrowser
from PyQt5.QtWidgets import (
    QApplication, QWizard, QWizardPage, QVBoxLayout, QHBoxLayout,
    QLabel, QCheckBox, QPushButton, QMessageBox, QInputDialog, QLineEdit, QTextEdit
)
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, QProcess, QTimer

CMD_MAPPING = {
    "Education": "sudo -S omnipkg put install maibloom-edupackage",
    "Programming": "sudo -S omnipkg put install maibloom-devpackage",
    "Office": "sudo -S omnipkg put install maibloom-officepackage",
    "Daily Use": "sudo -S omnipkg put install maibloom-dailypackage",
    "Gaming": "sudo -S omnipkg put install maibloom-gamingpackage"
}

class IntroPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Welcome to Mai Bloom OS Setup")
        self.setSubTitle("Select the packages you want to install based on your daily needs:")
        layout = QVBoxLayout()
        logo_label = QLabel()
        logo_pixmap = QPixmap("logo.png")
        logo_label.setPixmap(logo_pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)
        self.checkboxes = {}
        for option in CMD_MAPPING.keys():
            cb = QCheckBox(option)
            self.checkboxes[option] = cb
            layout.addWidget(cb)
        self.setLayout(layout)

class CommandPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Executing Commands")
        self.setSubTitle("Selected commands will execute and output will be shown in real time.")
        layout = QVBoxLayout()
        self.output_view = QTextEdit()
        self.output_view.setReadOnly(True)
        layout.addWidget(self.output_view)
        self.setLayout(layout)
        self.process = None
        self.command_list = []
        self.current_command_index = 0
        self.password = None

    def initializePage(self):
        wizard = self.wizard()
        self.command_list = []
        for option, cb in wizard.page(0).checkboxes.items():
            if cb.isChecked():
                self.command_list.append(CMD_MAPPING[option])
        if self.command_list:
            self.password, ok = QInputDialog.getText(
                self, "Sudo Password", "Please enter your sudo password:",
                QLineEdit.Password
            )
            if not ok or not self.password:
                self.output_view.setPlainText("Sudo password not provided. Aborting execution.")
                return
        else:
            self.output_view.setPlainText("No options were selected. Nothing to execute.")
            return

        self.current_command_index = 0
        QTimer.singleShot(100, self.execute_next_command)

    def execute_next_command(self):
        if self.current_command_index >= len(self.command_list):
            self.output_view.append("\nAll commands executed.")
            return
        cmd = self.command_list[self.current_command_index]
        self.output_view.append(f"\nExecuting: {cmd}\n")
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyRead.connect(self.handle_output)
        self.process.finished.connect(self.command_finished)
        self.process.started.connect(lambda: self.process.write((self.password + "\n").encode()))
        self.process.start(cmd)

    def handle_output(self):
        data = self.process.readAllStandardOutput().data().decode("utf-8")
        self.output_view.append(data)

    def command_finished(self, exitCode, exitStatus):
        self.output_view.append(f"\nFinished: {self.command_list[self.current_command_index]}\n")
        self.current_command_index += 1
        self.execute_next_command()

class FinalPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Enjoy!")
        self.setSubTitle("Thank you for setting up Mai Bloom OS.")
        layout = QVBoxLayout()
        logo_label = QLabel()
        logo_pixmap = QPixmap("logo.png")
        logo_label.setPixmap(logo_pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)
        info_label = QLabel("Welcome to Mai Bloom OS!\n\nFeel free to exit or learn more about our OS.")
        info_label.setAlignment(Qt.AlignCenter)
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
        QApplication.quit()
    
    def learn_more(self):
        webbrowser.open("https://example.com/maibloom")
        QMessageBox.information(self, "Learn More", "Visit the Mai Bloom OS website for more details!")

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet("""
        QWizard {
            background-color: #f8f8f8;
        }
        QWizardPage {
            font-family: Arial, sans-serif;
            font-size: 14px;
        }
        QLabel {
            margin: 10px;
        }
        QCheckBox {
            margin: 5px;
        }
        QPushButton {
            padding: 8px;
            margin: 10px;
            font-size: 14px;
        }
    """)
    wizard = QWizard()
    wizard.setWindowTitle("Welcome to Mai Bloom OS")
    wizard.setWindowIcon(QIcon("logo.png"))
    wizard.addPage(IntroPage())
    wizard.addPage(CommandPage())
    wizard.addPage(FinalPage())
    wizard.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
