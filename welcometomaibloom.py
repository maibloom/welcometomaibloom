import sys
import subprocess
import webbrowser
from PyQt5.QtWidgets import (
    QApplication, QWizard, QWizardPage, QVBoxLayout, QHBoxLayout,
    QLabel, QCheckBox, QPushButton, QMessageBox, QInputDialog, QLineEdit
)
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt

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
        self.setSubTitle("The selected commands will now execute.")
        layout = QVBoxLayout()
        self.status_label = QLabel("Preparing to run commands...")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        self.setLayout(layout)
    
    def initializePage(self):
        wizard = self.wizard()
        commands = []
        for option, cb in wizard.page(0).checkboxes.items():
            if cb.isChecked():
                commands.append(CMD_MAPPING[option])
        if commands:
            sudo_password, ok = QInputDialog.getText(
                self, "Sudo Password", "Please enter your sudo password:",
                QLineEdit.Password
            )
            if not ok or not sudo_password:
                self.status_label.setText("Sudo password not provided. Aborting execution.")
                return
        else:
            self.status_label.setText("No options were selected. Nothing to execute.")
            return

        output_lines = []
        for cmd in commands:
            try:
                proc = subprocess.Popen(
                    cmd, shell=True,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                out, err = proc.communicate(sudo_password + "\n")
                if out.strip():
                    output_lines.append(out.strip())
                elif err.strip():
                    output_lines.append(err.strip())
            except Exception as e:
                output_lines.append(f"Error executing '{cmd}': {e}")
        
        if output_lines:
            self.status_label.setText("Executed commands:\n" + "\n".join(output_lines))
        else:
            self.status_label.setText("Commands executed, but no output was returned.")

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
