import re
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel
from PyQt6.QtGui import QColor

class ResultTab(QWidget):
    pass

    def __init__(self, tr, is_error_table=False):
        super().__init__()
        self.tr = tr
        self.is_error_table = is_error_table
        self.current_lang = 'ru'
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.update_headers()
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setStyleSheet('\n            QTableWidget {\n                background-color: #1e1e1e;\n                color: #ffffff;\n                gridline-color: #555555;\n            }\n            QTableWidget::item:selected {\n                background-color: #42a5f5;\n            }\n            QHeaderView::section {\n                background-color: #2b2b2b;\n                color: #ffffff;\n                padding: 5px;\n                border: 1px solid #555555;\n            }\n        ')
        layout.addWidget(self.table)
        self.table.itemSelectionChanged.connect(self.on_row_selected)
        self.main_window = None

    def set_main_window(self, window):
        self.main_window = window

    def set_language(self, lang):
        self.current_lang = lang
        self.update_headers()

    def update_headers(self):
        self.table.setHorizontalHeaderLabels([self.tr('Условный код'), self.tr('Тип лексемы'), self.tr('Лексема'), self.tr('Местоположение')])

    def clear_results(self):
        self.table.setRowCount(0)

    def add_result(self, code, token_type, lexeme, location):
        row_count = self.table.rowCount()
        self.table.insertRow(row_count)
        self.table.setItem(row_count, 0, QTableWidgetItem(str(code)))
        self.table.setItem(row_count, 1, QTableWidgetItem(token_type))
        self.table.setItem(row_count, 2, QTableWidgetItem(lexeme))
        self.table.setItem(row_count, 3, QTableWidgetItem(location))
        if code == 99:
            for col in range(4):
                item = self.table.item(row_count, col)
                if item:
                    item.setForeground(QColor('#F48771'))

    def on_row_selected(self):
        if not self.main_window or not self.is_error_table:
            return
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            return
        row = self.table.currentRow()
        if row < 0:
            return
        location_item = self.table.item(row, 3)
        if not location_item:
            return
        location = location_item.text()
        if self.current_lang == 'ru':
            match = re.search('строка (\\d+), (\\d+)-\\d+', location)
        else:
            match = re.search('line (\\d+), (\\d+)-\\d+', location)
        if match:
            line = int(match.group(1))
            col = int(match.group(2))
            self.main_window.go_to_position(line, col)

class SyntaxErrorResultTab(QWidget):
    pass

    def __init__(self, tr):
        super().__init__()
        self.tr = tr
        self.current_lang = 'ru'
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.update_headers()
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setStyleSheet('\n            QTableWidget {\n                background-color: #1e1e1e;\n                color: #ffffff;\n                gridline-color: #555555;\n            }\n            QTableWidget::item:selected {\n                background-color: #42a5f5;\n            }\n            QHeaderView::section {\n                background-color: #2b2b2b;\n                color: #ffffff;\n                padding: 5px;\n                border: 1px solid #555555;\n            }\n        ')
        self.footer = QLabel()
        self.footer.setStyleSheet('color: #cccccc; padding: 6px 4px;')
        self._total_errors = 0
        self.set_total(0)
        layout.addWidget(self.table)
        layout.addWidget(self.footer)
        self.table.itemSelectionChanged.connect(self.on_row_selected)
        self.main_window = None

    def set_main_window(self, window):
        self.main_window = window

    def set_language(self, lang):
        self.current_lang = lang
        self.update_headers()
        self.set_total(self._total_errors)

    def update_headers(self):
        self.table.setHorizontalHeaderLabels([self.tr('Неверный фрагмент'), self.tr('Местоположение'), self.tr('Описание ошибки')])

    def clear_results(self):
        self.table.setRowCount(0)
        self.set_total(0)

    def set_total(self, n: int):
        self._total_errors = n
        self.footer.setText(f"{self.tr('Общее количество ошибок:')} {n}")

    def add_row(self, fragment: str, location: str, description: str):
        row = self.table.rowCount()
        self.table.insertRow(row)
        for col, text in enumerate((fragment, location, description)):
            item = QTableWidgetItem(text)
            item.setForeground(QColor('#F48771'))
            self.table.setItem(row, col, item)

    def on_row_selected(self):
        if not self.main_window:
            return
        row = self.table.currentRow()
        if row < 0:
            return
        location_item = self.table.item(row, 1)
        if not location_item:
            return
        location = location_item.text()
        if self.current_lang == 'ru':
            match = re.search('строка (\\d+), позиция (\\d+)', location)
        else:
            match = re.search('line (\\d+), position (\\d+)', location)
        if match:
            line = int(match.group(1))
            col = int(match.group(2))
            self.main_window.go_to_position(line, col)
