import sys
import time
import threading
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QApplication, QWidget, QTextEdit, QPushButton,
    QVBoxLayout, QLabel, QFileDialog, QSlider, QMessageBox, QHBoxLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QTextCharFormat, QFont, QSyntaxHighlighter
from pygments import lex
from pygments.lexers import guess_lexer, PythonLexer, CLexer, JavascriptLexer
from pygments.token import Token


class PygmentsHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.format = QTextCharFormat()
        self.format.setFont(QFont("Consolas", 11))
        self.lexer = PythonLexer()

    def set_language_by_text(self, text):
        try:
            self.lexer = guess_lexer(text)
        except:
            self.lexer = PythonLexer()

    def highlightBlock(self, text):
        for token, content in lex(text, self.lexer):
            fmt = QTextCharFormat(self.format)
            if token in Token.Comment:
                fmt.setForeground(QColor("#6A9955"))
            elif token in Token.Keyword:
                fmt.setForeground(QColor("#569CD6"))
            elif token in Token.String:
                fmt.setForeground(QColor("#CE9178"))
            elif token in Token.Name.Function:
                fmt.setForeground(QColor("#DCDCAA"))
            elif token in Token.Name.Class:
                fmt.setForeground(QColor("#4EC9B0"))
            elif token in Token.Operator:
                fmt.setForeground(QColor("#D4D4D4"))
            else:
                fmt.setForeground(QColor("#CCCCCC"))
            self.setFormat(text.find(content), len(content), fmt)


class CodeTyperApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Code Typer (just 4 fun)")
        self.setGeometry(200, 200, 300, 200)
        self.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4;")
        self.init_ui()
        self.paused = False
    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.pause_button.setText("▶️ Resume Typing")
        else:
            self.pause_button.setText("⏸️ Pause Typing")        

    def clear_target_file(self):
        path, _ = QFileDialog.getSaveFileName(self, "Select File to Clear", "", "Text Files (*.txt);;All Files (*)")
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write("")  # Empty the file
                QMessageBox.information(self, "Cleared", f"{path} has been cleared.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not clear file:\n{e}")


    def init_ui(self):
        layout = QVBoxLayout()

        self.instructions = QLabel("Paste your code below:")
        layout.addWidget(self.instructions)

        self.code_input = QTextEdit()
        self.code_input.setStyleSheet(
            "font-family: Consolas; font-size: 12pt; background-color: #252526; color: #d4d4d4;"
        )
        layout.addWidget(self.code_input)

        self.highlighter = PygmentsHighlighter(self.code_input.document())

        hbox = QHBoxLayout()

        self.load_button = QPushButton("📂 Load Template")
        self.load_button.clicked.connect(self.load_template)
        hbox.addWidget(self.load_button)

        self.save_button = QPushButton("💾 Save Template")
        self.save_button.clicked.connect(self.save_template)
        hbox.addWidget(self.save_button)

        layout.addLayout(hbox)

        self.slider_label = QLabel("Typing speed (milliseconds per character):")
        layout.addWidget(self.slider_label)

        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(10)
        self.speed_slider.setMaximum(1000)
        self.speed_slider.setValue(100)
        self.speed_slider.setTickInterval(10)
        layout.addWidget(self.speed_slider)

        self.start_button = QPushButton("📝 Start Typing into File")
        self.start_button.setStyleSheet("background-color: #0e639c; color: white;")
        self.start_button.clicked.connect(self.start_typing)
        layout.addWidget(self.start_button)

        self.pause_button = QPushButton("⏸️ Pause Typing")
        self.pause_button.setStyleSheet("background-color: #f39c12; color: black;")
        self.pause_button.setEnabled(False)
        self.pause_button.clicked.connect(self.toggle_pause)
        layout.addWidget(self.pause_button)

        self.clear_file_button = QPushButton("🧹 Clear Output File")
        self.clear_file_button.setStyleSheet("background-color: #c0392b; color: white;")
        self.clear_file_button.clicked.connect(self.clear_target_file)
        layout.addWidget(self.clear_file_button)



        self.setLayout(layout)

        # Update syntax highlighting when code is edited
        self.code_input.textChanged.connect(self.trigger_syntax_highlighting)
        self.syntax_timer = QTimer()
        self.syntax_timer.setInterval(500)  # 500ms delay after typing
        self.syntax_timer.setSingleShot(True)
        self.syntax_timer.timeout.connect(self.update_syntax_highlighting)

    def trigger_syntax_highlighting(self):
        self.syntax_timer.start()



    def update_syntax_highlighting(self):
        text = self.code_input.toPlainText()
        self.highlighter.set_language_by_text(text)
        self.highlighter.rehighlight()

    def load_template(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Code Template", "", "Code Files (*.py *.c *.cpp *.js *.txt)")
        if path:
            with open(path, "r", encoding="utf-8") as file:
                code = file.read()
                self.code_input.setPlainText(code)

    def save_template(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Code Template", "", "Text Files (*.txt)")
        if path:
            with open(path, "w", encoding="utf-8") as file:
                file.write(self.code_input.toPlainText())
            QMessageBox.information(self, "Saved", "Template saved successfully!")

    def start_typing(self):
        code = self.code_input.toPlainText().strip()
        if not code:
            QMessageBox.warning(self, "No Code", "Please paste some code first.")
            return

        filepath, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Text Files (*.txt);;All Files (*)")
        if not filepath:
            return

        delay = self.speed_slider.value() / 1000.0  # ms to seconds
        self.start_button.setEnabled(False)

        self.pause_button.setEnabled(True)
        self.paused = False

        threading.Thread(target=self.type_code_to_file, args=(code, filepath, delay), daemon=True).start()

    def type_code_to_file(self, code, filepath, delay):
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                for char in code:
                    while self.paused:
                        time.sleep(0.1)
                    f.write(char)
                    f.flush()
                    time.sleep(delay)

            #self.show_done_message()
        except Exception as e:
            self.show_error(str(e))
        finally:
            self.start_button.setEnabled(True)
            self.pause_button.setEnabled(False)
            self.pause_button.setText("⏸️ Pause Typing")




    #def show_done_message(self):
        #QMessageBox.information(self, "Done", "Typing complete!")

    def show_error(self, message):
        QMessageBox.critical(self, "Error", f"An error occurred:\n{message}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = CodeTyperApp()
    window.show()
    sys.exit(app.exec_())
