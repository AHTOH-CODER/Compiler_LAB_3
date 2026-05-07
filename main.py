import sys
import os
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from scanner import Scanner
from translator import Translator

try:
    from antlr_parser_adapter import ANTLRParserAdapter
    HAS_ANTLR = True
except ImportError:
    HAS_ANTLR = False


def suppress_console_output():
    # В режиме GUI не выводим служебные сообщения в консоль.
    try:
        devnull = open(os.devnull, 'w', encoding='utf-8')
        sys.stdout = devnull
        sys.stderr = devnull
    except Exception:
        pass


class SyntaxErrorHighlight(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.error_positions = []
        self.active_error_index = -1
        self.error_format = QTextCharFormat()
        self.error_format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.WaveUnderline)
        self.error_format.setUnderlineColor(QColor('#FF4444'))
        self.error_format.setBackground(QColor('#44FF4444'))
        self.active_error_format = QTextCharFormat()
        self.active_error_format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.WaveUnderline)
        self.active_error_format.setUnderlineColor(QColor('#FF0000'))
        self.active_error_format.setBackground(QColor('#88FF6666'))
        self.active_error_format.setFontWeight(QFont.Weight.Bold)

    def set_errors(self, errors, active_index=-1):
        self.error_positions = []
        for e in errors:
            if isinstance(e, dict):
                line = e.get('line', 1)
                col = e.get('col', 1)
                fragment = e.get('fragment', '')
            else:
                line = getattr(e, 'line', 1)
                col = getattr(e, 'col', 1)
                fragment = getattr(e, 'fragment', '')
            self.error_positions.append((line, col, len(str(fragment))))
        self.active_error_index = active_index
        self.rehighlight()
        if self.parent() and hasattr(self.parent(), 'parent'):
            view = self.parent().parent()
            if view and hasattr(view, 'viewport'):
                view.viewport().update()

    def clear_errors(self):
        self.error_positions = []
        self.active_error_index = -1
        self.rehighlight()

    def highlightBlock(self, text):
        block_number = self.currentBlock().blockNumber() + 1
        for i, (line, col, length) in enumerate(self.error_positions):
            if line == block_number:
                fmt = self.active_error_format if i == self.active_error_index else self.error_format
                self.setFormat(col - 1, max(length, 1), fmt)


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QSize(self.code_editor.line_number_width(), 0)

    def paintEvent(self, event):
        self.code_editor.lineNumberAreaPaintEvent(event)


class CodeEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.update_line_number_area_width()
        self.highlight_current_line()
        self.setAcceptDrops(True)

    def line_number_width(self):
        digits = len(str(self.blockCount()))
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self):
        self.setViewportMargins(self.line_number_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_width(), cr.height()))

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(40, 44, 52))
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor(220, 220, 220))
                painter.drawText(0, int(top), self.line_number_area.width() - 2,
                                 self.fontMetrics().height(), Qt.AlignmentFlag.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def highlight_current_line(self):
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor(50, 55, 65)
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.endswith('.txt'):
                main_window = None
                for widget in QApplication.topLevelWidgets():
                    if isinstance(widget, TextEditor):
                        main_window = widget
                        break
                if main_window:
                    main_window.open_file_with_path(file_path)
                    break


class SyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []
        keywords = [
            # Поддерживаемая конструкция варианта 8 (Scala)
            'val', 'Complex'
        ]
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor('#FFA500'))
        keyword_format.setFontWeight(QFont.Weight.Bold)
        for keyword in keywords:
            pattern = QRegularExpression(r'\b' + keyword + r'\b')
            rule = (pattern, keyword_format)
            self.highlighting_rules.append(rule)
        string_format = QTextCharFormat()
        string_format.setForeground(QColor('#98FB98'))
        pattern = QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"|\'[^\'\\]*(\\.[^\'\\]*)*\'')
        rule = (pattern, string_format)
        self.highlighting_rules.append(rule)
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor('#BC8F8F'))
        pattern = QRegularExpression(r'//.*')
        rule = (pattern, comment_format)
        self.highlighting_rules.append(rule)
        number_format = QTextCharFormat()
        number_format.setForeground(QColor('#B5CEA8'))
        pattern = QRegularExpression(r'\b[0-9]+(\.[0-9]+)?i?\b')
        rule = (pattern, number_format)
        self.highlighting_rules.append(rule)

    def highlightBlock(self, text):
        for pattern, fmt in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)


class EditorTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.code_editor = CodeEditor()
        self.code_editor.setStyleSheet("""
            QPlainTextEdit {
                border: 2px solid #FFA500;
                border-radius: 5px;
                background-color: #1e1e1e;
                selection-background-color: #FFA500;
            }
        """)
        self.highlighter = SyntaxHighlighter(self.code_editor.document())
        self.error_highlighter = SyntaxErrorHighlight(self.code_editor.document())
        self.code_editor.textChanged.connect(self.text_changed)
        layout.addWidget(self.code_editor)
        self.current_file = None
        self.text_modified = False

    def text_changed(self):
        self.text_modified = True

    def get_text(self):
        return self.code_editor.toPlainText()

    def set_text(self, text):
        self.code_editor.setPlainText(text)
        self.text_modified = False


class TokenResultTab(QWidget):
    def __init__(self, tr):
        super().__init__()
        self.tr = tr
        self.current_lang = 'ru'
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.update_headers()
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                gridline-color: #FFA500;
                border: 2px solid #FFA500;
                border-radius: 5px;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #FFA500;
                color: #000000;
            }
            QHeaderView::section {
                background-color: #404040;
                color: #FFA500;
                padding: 8px;
                border: 1px solid #FFA500;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.table)

    def set_language(self, lang):
        self.current_lang = lang
        self.update_headers()

    def update_headers(self):
        self.table.setHorizontalHeaderLabels([
            self.tr('Тип'),
            self.tr('Фрагмент'),
            self.tr('Местоположение'),
            self.tr('Описание'),
        ])

    def clear_results(self):
        self.table.setRowCount(0)

    def add_result(self, code, token_type, lexeme, location):
        row_count = self.table.rowCount()
        self.table.insertRow(row_count)
        self.table.setItem(row_count, 0, QTableWidgetItem(str(code)))
        self.table.setItem(row_count, 1, QTableWidgetItem(token_type))
        self.table.setItem(row_count, 2, QTableWidgetItem(lexeme))
        self.table.setItem(row_count, 3, QTableWidgetItem(location))


class ErrorResultTab(QWidget):
    def __init__(self, tr):
        super().__init__()
        self.tr = tr
        self.current_lang = 'ru'
        self.main_window = None
        self.errors_data = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.update_headers()
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                gridline-color: #FFA500;
                border: 2px solid #FFA500;
                border-radius: 5px;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #FFA500;
                color: #000000;
            }
            QHeaderView::section {
                background-color: #404040;
                color: #FFA500;
                padding: 8px;
                border: 1px solid #FFA500;
                font-weight: bold;
            }
        """)
        self.footer = QLabel()
        self.footer.setStyleSheet("color: #FFA500; padding: 6px 4px; font-weight: bold;")
        layout.addWidget(self.table)
        layout.addWidget(self.footer)
        self.table.itemSelectionChanged.connect(self.on_row_selected)

    def set_main_window(self, window):
        self.main_window = window

    def set_language(self, lang):
        self.current_lang = lang
        self.update_headers()

    def update_headers(self):
        self.table.setHorizontalHeaderLabels([
            self.tr('Тип'),
            self.tr('Фрагмент'),
            self.tr('Местоположение'),
            self.tr('Описание'),
            self.tr('Строка')
        ])

    def clear_results(self):
        self.table.setRowCount(0)
        self.errors_data = []
        self.footer.setText("")

    def add_error(self, error_type, fragment, location, description):
        row_count = self.table.rowCount()
        self.table.insertRow(row_count)
        items = [
            QTableWidgetItem(error_type),
            QTableWidgetItem(fragment),
            QTableWidgetItem(location),
            QTableWidgetItem(description),
        ]
        for col, item in enumerate(items):
            item.setForeground(QColor('#F48771'))
            self.table.setItem(row_count, col, item)
        self.errors_data.append({
            'type': error_type,
            'fragment': fragment,
            'location': location,
            'description': description,
            'row': row_count
        })
        self.footer.setText(f"{self.tr('Всего ошибок:')} {row_count + 1}")
    
    def on_row_selected(self):
        if not self.main_window:
            return
        row = self.table.currentRow()
        if row < 0 or row >= len(self.errors_data):
            return
        err = self.errors_data[row]
        location = err['location']
        import re
        if self.current_lang == 'ru':
            match = re.search(r'строка (\d+), позиция (\d+)', location)
        else:
            match = re.search(r'line (\d+), position (\d+)', location)
        if match:
            line = int(match.group(1))
            col = int(match.group(2))
            self.main_window.go_to_position(line, col, row)


class TextEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.translator = Translator()
        self.tr = self.translator.tr
        self.current_font_size = 11
        self.result_font_size = 10
        self.scanner = Scanner()
        self.use_antlr_parser = False
        self.initUI()
        self.retranslateUi()
        self.editor_tabs.currentChanged.connect(self.update_cursor_position)

    def initUI(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
            }
            QTabWidget::pane {
                border: 2px solid #FFA500;
                border-radius: 5px;
                top: -1px;
            }
            QTabBar::tab {
                background-color: #404040;
                color: #ffffff;
                padding: 8px 12px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: #FFA500;
                color: #000000;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background-color: #606060;
            }
        """)
        self.editor_tabs = QTabWidget()
        self.editor_tabs.setTabsClosable(True)
        self.editor_tabs.tabCloseRequested.connect(self.close_editor_tab)
        self.result_tabs = QTabWidget()
        self.text_result_tab = QWidget()
        text_result_layout = QVBoxLayout(self.text_result_tab)
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 2px solid #FFA500;
                border-radius: 5px;
                padding: 5px;
                selection-background-color: #FFA500;
            }
        """)
        text_result_layout.addWidget(self.result_text)
        self.tokens_tab = TokenResultTab(self.tr)
        self.error_table_tab = ErrorResultTab(self.tr)
        self.error_table_tab.set_main_window(self)
        self.result_tabs.addTab(self.text_result_tab, self.tr("Текстовый вывод"))
        self.result_tabs.addTab(self.tokens_tab, self.tr("Лексемы"))
        self.result_tabs.addTab(self.error_table_tab, self.tr("Ошибки"))
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self.editor_tabs)
        splitter.addWidget(self.result_tabs)
        splitter.setSizes([400, 300])
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #FFA500;
                height: 3px;
            }
            QSplitter::handle:hover {
                background-color: #FFB52E;
            }
        """)
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(splitter)
        self.setCentralWidget(central)
        self.add_new_editor_tab()
        self.create_menu()
        self.create_toolbar()
        self.create_status_bar()
        self.setWindowTitle(self.tr("Текстовый редактор с языковым процессором"))
        self.resize(1000, 700)
        self.setMinimumSize(600, 400)

    def create_status_bar(self):
        self.status_bar = self.statusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #404040;
                color: #FFA500;
                border-top: 2px solid #FFA500;
                font-weight: bold;
            }
        """)
        self.status_bar.showMessage(self.tr('Готов'))
        self.cursor_position_label = QLabel(self.tr('Строка: 1, Столбец: 1'))
        self.file_info_label = QLabel(self.tr('Новый файл'))
        self.encoding_label = QLabel(self.tr('UTF-8'))
        self.parser_type_label = QLabel("Parser: Python")
        self.parser_type_label.setStyleSheet("color: #FFA500; font-weight: bold; margin-right: 10px;")
        self.status_bar.addPermanentWidget(self.parser_type_label)
        self.status_bar.addPermanentWidget(self.cursor_position_label)
        self.status_bar.addPermanentWidget(self.file_info_label)
        self.status_bar.addPermanentWidget(self.encoding_label)

    def update_cursor_position(self):
        editor = self.get_current_editor()
        if not editor:
            self.cursor_position_label.setText(self.tr('Строка: -, Столбец: -'))
            return
        cursor = editor.code_editor.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        self.cursor_position_label.setText(f"{self.tr('Строка:')} {line}, {self.tr('Столбец:')} {col}")

    def update_file_info(self, file_name):
        if file_name:
            self.file_info_label.setText(os.path.basename(file_name))
        else:
            self.file_info_label.setText(self.tr('Новый файл'))

    def get_current_editor(self):
        return self.editor_tabs.currentWidget()

    def add_new_editor_tab(self, file_name=None, content=''):
        new_tab = EditorTab()
        if content:
            new_tab.set_text(content)
        base_name = self.tr('Новый файл')
        tab_name = os.path.basename(file_name) if file_name else f'{base_name} {self.editor_tabs.count() + 1}'
        index = self.editor_tabs.addTab(new_tab, tab_name)
        self.editor_tabs.setCurrentIndex(index)
        if file_name:
            new_tab.current_file = file_name
        new_tab.code_editor.cursorPositionChanged.connect(self.update_cursor_position)
        new_tab.code_editor.textChanged.connect(self.on_tab_text_changed)
        return new_tab

    def on_tab_text_changed(self):
        index = self.editor_tabs.currentIndex()
        tab_text = self.editor_tabs.tabText(index)
        if not tab_text.endswith('*'):
            self.editor_tabs.setTabText(index, tab_text + '*')

    def close_editor_tab(self, index):
        if self.editor_tabs.count() <= 1:
            return
        tab = self.editor_tabs.widget(index)
        if tab.text_modified:
            reply = QMessageBox.question(
                self, self.tr('Сохранение'),
                self.tr('Сохранить изменения в документе?'),
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Save:
                self.save_current_file()
            elif reply == QMessageBox.StandardButton.Cancel:
                return
        self.editor_tabs.removeTab(index)

    def change_editor_font_size(self, delta):
        self.current_font_size = max(8, min(72, self.current_font_size + delta))
        editor = self.get_current_editor()
        if editor:
            font = editor.code_editor.font()
            font.setPointSize(self.current_font_size)
            editor.code_editor.setFont(font)
            editor.code_editor.update_line_number_area_width()
        self.status_bar.showMessage(f"{self.tr('Размер шрифта редактора:')} {self.current_font_size}")

    def change_result_font_size(self, delta):
        self.result_font_size = max(8, min(72, self.result_font_size + delta))
        font = self.result_text.font()
        font.setPointSize(self.result_font_size)
        self.result_text.setFont(font)
        self.status_bar.showMessage(f"{self.tr('Размер шрифта результатов:')} {self.result_font_size}")

    def create_menu(self):
        menubar = self.menuBar()
        menubar.clear()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #404040;
                color: #ffffff;
                border-bottom: 2px solid #FFA500;
            }
            QMenuBar::item:selected {
                background-color: #FFA500;
                color: #000000;
            }
            QMenu {
                background-color: #404040;
                color: #ffffff;
                border: 2px solid #FFA500;
            }
            QMenu::item:selected {
                background-color: #FFA500;
                color: #000000;
            }
        """)
        file_menu = menubar.addMenu(self.tr('Файл'))
        new_act = QAction(self.tr('Создать'), self)
        new_act.setShortcut('Ctrl+N')
        new_act.triggered.connect(lambda: self.add_new_editor_tab())
        file_menu.addAction(new_act)
        open_act = QAction(self.tr('Открыть'), self)
        open_act.setShortcut('Ctrl+O')
        open_act.triggered.connect(self.open_file)
        file_menu.addAction(open_act)
        save_act = QAction(self.tr('Сохранить'), self)
        save_act.setShortcut('Ctrl+S')
        save_act.triggered.connect(self.save_file)
        file_menu.addAction(save_act)
        save_as_act = QAction(self.tr('Сохранить как'), self)
        save_as_act.setShortcut('Ctrl+Shift+S')
        save_as_act.triggered.connect(self.save_as_file)
        file_menu.addAction(save_as_act)
        file_menu.addSeparator()
        exit_act = QAction(self.tr('Выход'), self)
        exit_act.setShortcut('Ctrl+Q')
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)
        edit_menu = menubar.addMenu(self.tr('Правка'))
        undo_act = QAction(self.tr('Отменить'), self)
        undo_act.setShortcut('Ctrl+Z')
        undo_act.triggered.connect(lambda: self.get_current_editor().code_editor.undo() if self.get_current_editor() else None)
        edit_menu.addAction(undo_act)
        redo_act = QAction(self.tr('Повторить'), self)
        redo_act.setShortcut('Ctrl+Y')
        redo_act.triggered.connect(lambda: self.get_current_editor().code_editor.redo() if self.get_current_editor() else None)
        edit_menu.addAction(redo_act)
        edit_menu.addSeparator()
        cut_act = QAction(self.tr('Вырезать'), self)
        cut_act.setShortcut('Ctrl+X')
        cut_act.triggered.connect(lambda: self.get_current_editor().code_editor.cut() if self.get_current_editor() else None)
        edit_menu.addAction(cut_act)
        copy_act = QAction(self.tr('Копировать'), self)
        copy_act.setShortcut('Ctrl+C')
        copy_act.triggered.connect(lambda: self.get_current_editor().code_editor.copy() if self.get_current_editor() else None)
        edit_menu.addAction(copy_act)
        paste_act = QAction(self.tr('Вставить'), self)
        paste_act.setShortcut('Ctrl+V')
        paste_act.triggered.connect(lambda: self.get_current_editor().code_editor.paste() if self.get_current_editor() else None)
        edit_menu.addAction(paste_act)
        del_act = QAction(self.tr('Удалить'), self)
        del_act.setShortcut('Del')
        del_act.triggered.connect(lambda: self.get_current_editor().code_editor.textCursor().removeSelectedText() if self.get_current_editor() else None)
        edit_menu.addAction(del_act)
        sel_all_act = QAction(self.tr('Выделить все'), self)
        sel_all_act.setShortcut('Ctrl+A')
        sel_all_act.triggered.connect(lambda: self.get_current_editor().code_editor.selectAll() if self.get_current_editor() else None)
        edit_menu.addAction(sel_all_act)
        view_menu = menubar.addMenu(self.tr('Вид'))
        inc_ed_font = QAction(self.tr('Увеличить шрифт редактора'), self)
        inc_ed_font.setShortcut('Ctrl+=')
        inc_ed_font.triggered.connect(lambda: self.change_editor_font_size(1))
        view_menu.addAction(inc_ed_font)
        dec_ed_font = QAction(self.tr('Уменьшить шрифт редактора'), self)
        dec_ed_font.setShortcut('Ctrl+-')
        dec_ed_font.triggered.connect(lambda: self.change_editor_font_size(-1))
        view_menu.addAction(dec_ed_font)
        view_menu.addSeparator()
        inc_res_font = QAction(self.tr('Увеличить шрифт результатов'), self)
        inc_res_font.setShortcut('Ctrl+Shift+=')
        inc_res_font.triggered.connect(lambda: self.change_result_font_size(1))
        view_menu.addAction(inc_res_font)
        dec_res_font = QAction(self.tr('Уменьшить шрифт результатов'), self)
        dec_res_font.setShortcut('Ctrl+Shift+-')
        dec_res_font.triggered.connect(lambda: self.change_result_font_size(-1))
        view_menu.addAction(dec_res_font)
        text_menu = menubar.addMenu(self.tr('Текст'))
        text_items = [
            'Постановка задачи', 'Грамматика', 'Классификация грамматики',
            'Метод анализа', 'Тестовый пример', 'Список литературы',
            'Исходный код программы'
        ]
        for item in text_items:
            act = QAction(self.tr(item), self)
            act.triggered.connect(lambda _, t=item: self.show_text_info(t))
            text_menu.addAction(act)
        parser_menu = menubar.addMenu("Parser")
        python_act = QAction("Python (automaton)", self)
        python_act.triggered.connect(lambda: self.set_parser(False))
        parser_menu.addAction(python_act)
        antlr_act = QAction("ANTLR", self)
        antlr_act.triggered.connect(lambda: self.set_parser(True))
        parser_menu.addAction(antlr_act)
        run_menu = menubar.addMenu(self.tr('Пуск'))
        run_act = QAction(self.tr('Запуск анализатора'), self)
        run_act.setShortcut('F5')
        run_act.triggered.connect(self.start_analyzer)
        run_menu.addAction(run_act)
        help_menu = menubar.addMenu(self.tr('Справка'))
        help_act = QAction(self.tr('Вызов справки'), self)
        help_act.setShortcut('F1')
        help_act.triggered.connect(self.show_help)
        help_menu.addAction(help_act)
        about_act = QAction(self.tr('О программе'), self)
        about_act.triggered.connect(self.show_about)
        help_menu.addAction(about_act)
        lang_menu = menubar.addMenu(self.tr('Язык'))
        ru_act = QAction(self.tr('Русский'), self)
        ru_act.triggered.connect(lambda: self.change_language('ru'))
        lang_menu.addAction(ru_act)
        en_act = QAction(self.tr('English'), self)
        en_act.triggered.connect(lambda: self.change_language('en'))
        lang_menu.addAction(en_act)

    def create_toolbar(self):
        self.toolbar = self.addToolBar(self.tr('Инструменты'))
        self.toolbar.setMovable(False)
        self.toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.toolbar.setStyleSheet("""
            QToolBar {
                background-color: #404040;
                border-bottom: 2px solid #FFA500;
                spacing: 5px;
            }
            QToolButton {
                background-color: #505050;
                color: #ffffff;
                border: 1px solid #FFA500;
                border-radius: 3px;
                padding: 5px;
                min-width: 60px;
            }
            QToolButton:hover {
                background-color: #FFA500;
                color: #000000;
            }
            QToolButton:pressed {
                background-color: #FFB52E;
            }
        """)
        self.update_toolbar()

    def update_toolbar(self):
        self.toolbar.clear()

        def create_icon(name):
            if name == 'system-run':
                pixmap = QPixmap(24, 24)
                pixmap.fill(Qt.GlobalColor.transparent)
                painter = QPainter(pixmap)
                painter.setBrush(QColor(255, 165, 0))
                painter.setPen(Qt.PenStyle.NoPen)
                points = [QPoint(6, 4), QPoint(20, 12), QPoint(6, 20)]
                painter.drawPolygon(*points)
                painter.end()
                return QIcon(pixmap)
            elif name == 'help-contents':
                pixmap = QPixmap(24, 24)
                pixmap.fill(Qt.GlobalColor.transparent)
                painter = QPainter(pixmap)
                painter.setBrush(QColor(255, 165, 0))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(4, 4, 16, 16)
                painter.setPen(QColor(255, 255, 255))
                painter.setFont(QFont('Arial', 12, QFont.Weight.Bold))
                painter.drawText(8, 18, '?')
                painter.end()
                return QIcon(pixmap)
            elif name == 'help-about':
                pixmap = QPixmap(24, 24)
                pixmap.fill(Qt.GlobalColor.transparent)
                painter = QPainter(pixmap)
                painter.setBrush(QColor(255, 165, 0))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(4, 4, 16, 16)
                painter.setPen(QColor(255, 255, 255))
                painter.setFont(QFont('Arial', 12, QFont.Weight.Bold))
                painter.drawText(11, 18, 'i')
                painter.end()
                return QIcon(pixmap)
            else:
                return QIcon.fromTheme(name)

        actions = [
            ('document-new', self.tr('Создать'), lambda: self.add_new_editor_tab()),
            ('document-open', self.tr('Открыть'), self.open_file),
            ('document-save', self.tr('Сохранить'), self.save_file),
            None,
            ('edit-undo', self.tr('Отменить'), lambda: self.get_current_editor().code_editor.undo() if self.get_current_editor() else None),
            ('edit-redo', self.tr('Повторить'), lambda: self.get_current_editor().code_editor.redo() if self.get_current_editor() else None),
            None,
            ('edit-copy', self.tr('Копировать'), lambda: self.get_current_editor().code_editor.copy() if self.get_current_editor() else None),
            ('edit-cut', self.tr('Вырезать'), lambda: self.get_current_editor().code_editor.cut() if self.get_current_editor() else None),
            ('edit-paste', self.tr('Вставить'), lambda: self.get_current_editor().code_editor.paste() if self.get_current_editor() else None),
            None,
            ('system-run', self.tr('Запуск'), self.start_analyzer),
            ('help-contents', self.tr('Справка'), self.show_help),
            ('help-about', self.tr('О программе'), self.show_about),
        ]
        for item in actions:
            if item is None:
                self.toolbar.addSeparator()
                continue
            icon_name, text, func = item
            icon = create_icon(icon_name)
            act = QAction(icon, text, self)
            act.triggered.connect(func)
            self.toolbar.addAction(act)

    def retranslateUi(self):
        self.setWindowTitle(self.tr("Текстовый редактор с языковым процессором"))
        menubar = self.menuBar()
        menubar.clear()
        self.create_menu()
        self.result_tabs.setTabText(0, self.tr("Текстовый вывод"))
        self.result_tabs.setTabText(1, self.tr("Лексемы"))
        self.result_tabs.setTabText(2, self.tr("Ошибки"))
        self.tokens_tab.update_headers()
        self.error_table_tab.update_headers()
        self.status_bar.showMessage(self.tr('Готов'))
        self.update_cursor_position()
        self.update_file_info(None)
        for i in range(self.editor_tabs.count()):
            tab = self.editor_tabs.widget(i)
            if tab and not tab.current_file:
                current_text = self.editor_tabs.tabText(i).rstrip('*')
                if current_text.startswith('Новый файл') or current_text.startswith('Untitled'):
                    base_name = self.tr('Новый файл')
                    if current_text == 'Новый файл' or current_text == 'Untitled':
                        new_text = base_name
                    else:
                        try:
                            num = current_text.split()[-1]
                            new_text = f"{base_name} {num}"
                        except:
                            new_text = base_name
                    if self.editor_tabs.tabText(i).endswith('*'):
                        new_text += '*'
                    self.editor_tabs.setTabText(i, new_text)
        self.update_toolbar()

    def change_language(self, lang):
        self.translator.set_language(lang)
        self.retranslateUi()
        self.tokens_tab.set_language(lang)
        self.error_table_tab.set_language(lang)
        tab = self.get_current_editor()
        if tab and tab.get_text().strip():
            self.start_analyzer()
        QMessageBox.information(
            self,
            self.tr('Смена языка'),
            self.tr('Язык изменен на русский') if lang == 'ru' else self.tr('Язык изменен на английский')
        )

    def set_parser(self, use_antlr):
        self.use_antlr_parser = use_antlr
        name = "ANTLR" if use_antlr else "Python"
        self.parser_type_label.setText(f"Parser: {name}")
        QMessageBox.information(self, "Parser", f"Selected: {name}")

    def open_file_with_path(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            self.add_new_editor_tab(file_path, content)
            self.status_bar.showMessage(f"{self.tr('Открыт файл:')} {file_path}")
            self.update_file_info(file_path)
        except Exception as e:
            QMessageBox.critical(self, self.tr('Ошибка'), f"{self.tr('Не удалось открыть файл:')} {str(e)}")

    def open_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, self.tr('Открыть файл'), '',
            'Текстовые файлы (*.txt);;Все файлы (*)'
        )
        if file_name:
            self.open_file_with_path(file_name)

    def save_current_file(self):
        tab = self.get_current_editor()
        if not tab:
            return
        if tab.current_file:
            try:
                with open(tab.current_file, 'w', encoding='utf-8') as file:
                    file.write(tab.get_text())
                tab.text_modified = False
                idx = self.editor_tabs.currentIndex()
                title = self.editor_tabs.tabText(idx)
                if title.endswith('*'):
                    self.editor_tabs.setTabText(idx, title[:-1])
                self.status_bar.showMessage(f"{self.tr('Файл сохранен:')} {tab.current_file}")
            except Exception as e:
                QMessageBox.critical(self, self.tr('Ошибка'), f"{self.tr('Не удалось сохранить файл:')} {str(e)}")
        else:
            self.save_as_file()

    def save_file(self):
        self.save_current_file()

    def save_as_file(self):
        file_name, _ = QFileDialog.getSaveFileName(
            self, self.tr('Сохранить как'), '',
            'Текстовые файлы (*.txt);;Все файлы (*)'
        )
        if file_name:
            tab = self.get_current_editor()
            if tab:
                tab.current_file = file_name
                self.save_current_file()
                self.editor_tabs.setTabText(self.editor_tabs.currentIndex(), os.path.basename(file_name))
                self.update_file_info(file_name)

    def show_text_info(self, text_type):
        info_texts = {
            'Постановка задачи': (
                'Разработать лексический и синтаксический анализатор для объявления комплексного числа '
                'в языке Scala (вариант 8) и интегрировать его в текстовый редактор.'
            ),
            'Грамматика': (
                "Поддерживается единственная конструкция объявления:\n"
                "val <id> = Complex(<num>, <num>);"
            ),
            'Классификация грамматики': 'Грамматика является автоматной (праворекурсивные продукции).',
            'Метод анализа': 'Конечный автомат с нейтрализацией ошибок (синхронизация по токену \';\').',
            'Тестовый пример': 'val z = Complex(1.5, 2.5);',
            'Список литературы': '1. Ахо А., Сети Р., Ульман Дж. Компиляторы.\n2. Scala Language Specification.',
            'Исходный код программы': 'main.py, scanner.py, parser.py, ScalaComplex.g4, antlr_parser_adapter.py'
        }
        QMessageBox.information(self, self.tr(text_type), info_texts[text_type])

    def go_to_position(self, line, col, error_index=-1):
        editor = self.get_current_editor()
        if not editor:
            return
        cursor = editor.code_editor.textCursor()
        block = editor.code_editor.document().findBlockByNumber(line - 1)
        if not block.isValid():
            return
        cursor.setPosition(block.position())
        target_pos = block.position() + col - 1
        if target_pos > len(editor.code_editor.toPlainText()):
            target_pos = block.position()
        cursor.setPosition(target_pos, QTextCursor.MoveMode.MoveAnchor)
        editor.code_editor.setTextCursor(cursor)
        editor.code_editor.setFocus()
        editor.code_editor.centerCursor()
        if error_index >= 0:
            editor.error_highlighter.active_error_index = error_index
            editor.error_highlighter.rehighlight()

    def start_analyzer(self):
        tab = self.get_current_editor()
        if not tab:
            return
        text = tab.get_text()
        self.tokens_tab.clear_results()
        self.error_table_tab.clear_results()
        tab.error_highlighter.clear_errors()
        if not text.strip():
            self.result_text.setPlainText(self.tr('Текст для анализа отсутствует.'))
            return
        results = self.scanner.analyze(text)
        current_lang = self.translator.lang
        if current_lang == 'ru':
            tokens_text = f"=== РЕЗУЛЬТАТЫ ЛЕКСИЧЕСКОГО АНАЛИЗА ===\n\n"
        else:
            tokens_text = f"=== LEXICAL ANALYSIS RESULTS ===\n\n"
        tokens_text += f"{self.tr('Найдено лексем:')} {len(results['tokens'])}\n"
        tokens_text += f"{self.tr('Найдено ошибок:')} {len(results['errors'])}\n\n"
        if results['tokens']:
            tokens_text += f"{self.tr('Список лексем:')}\n"
            tokens_text += "-" * 80 + "\n"
            for token in results['tokens']:
                display_type = token.get_display_type(current_lang)
                display_value = token.get_display_value(current_lang)
                if current_lang == 'ru':
                    location = f"строка {token.line:2d}, {token.start:2d}-{token.end:2d}"
                else:
                    location = f"line {token.line:2d}, {token.start:2d}-{token.end:2d}"
                tokens_text += f"{token.code:3d} | {display_type:22} | '{display_value:12}' | {location}\n"
        if results['errors']:
            tokens_text += f"\n{self.tr('Список лексических ошибок:')}\n"
            tokens_text += "-" * 80 + "\n"
            for error in results['errors']:
                if current_lang == 'ru':
                    tokens_text += f"{self.tr('Строка')} {error.line:2d}, {self.tr('Позиция')} {error.start:2d}: {error.value}\n"
                else:
                    tokens_text += f"Line {error.line:2d}, Position {error.start:2d}: {error.value}\n"
        if self.use_antlr_parser and HAS_ANTLR:
            parser_name = "ANTLR"
            try:
                parse_result = ANTLRParserAdapter(text, lang=current_lang).parse()
            except Exception as e:
                from parser import SyntaxErrorRecord, ParseResult
                parse_result = ParseResult(
                    ok=False,
                    errors=[SyntaxErrorRecord(
                        fragment="ERROR", line=1, col=1,
                        message=f"ANTLR error: {str(e)}"
                    )]
                )
        else:
            from parser import Parser
            parser_name = "Python"
            parse_result = Parser(results['tokens'], lang=current_lang).parse()
        tokens_text += f"\n\n{'=' * 50}\n"
        tokens_text += f"СИНТАКСИЧЕСКИЙ АНАЛИЗ [{parser_name}]\n"
        tokens_text += f"{'=' * 50}\n"
        if parse_result.ok:
            tokens_text += f"Синтаксических ошибок не обнаружено.\n"
        else:
            tokens_text += f"Найдено синтаксических ошибок: {len(parse_result.errors)}\n"
            for i, err in enumerate(parse_result.errors, 1):
                loc = err.location_ru() if current_lang == 'ru' else err.location_en()
                tokens_text += f"  {i}. [{loc}] {err.fragment}: {err.message}\n"
        self.result_text.setPlainText(tokens_text)
        for token in results['tokens']:
            self.tokens_tab.add_result(*token.to_table_row(current_lang))
        all_errors = []
        for error in results['errors']:
            if current_lang == 'ru':
                location = f"строка {error.line}, позиция {error.start}"
            else:
                location = f"line {error.line}, position {error.start}"
            all_errors.append({
                'type': 'Lexical',
                'fragment': error.value,
                'location': location,
                'description': error.value,
                'line': error.line,
                'col': error.start
            })
        for err in parse_result.errors:
            loc = err.location_ru() if current_lang == 'ru' else err.location_en()
            all_errors.append({
                'type': 'Syntax',
                'fragment': err.fragment,
                'location': loc,
                'description': err.message,
                'line': err.line,
                'col': err.col
            })
        for err in all_errors:
            self.error_table_tab.add_error(
                err['type'],
                err['fragment'],
                err['location'],
                err['description']
            )
        tab.error_highlighter.set_errors(all_errors)
        self.status_bar.showMessage(
            f"{self.tr('Анализ завершен')}. "
            f"{self.tr('Лексем:')} {len(results['tokens'])}, "
            f"{self.tr('Ошибок всего:')} {len(all_errors)}"
        )

    def show_help(self):
        help_text = self.tr('=== СПРАВКА ПО ТЕКСТОВОМУ РЕДАКТОРУ ===') + '\n\n' + \
                    self.tr('Функции меню "Файл":') + '\n' + \
                    "- " + self.tr('Создать') + ": " + self.tr('Создать новый документ (Ctrl+N)') + "\n" + \
                    "- " + self.tr('Открыть') + ": " + self.tr('Открыть существующий текстовый файл (Ctrl+O)') + "\n" + \
                    "- " + self.tr('Сохранить') + ": " + self.tr('Сохранить текущий документ (Ctrl+S)') + "\n" + \
                    "- " + self.tr('Сохранить как') + ": " + self.tr('Сохранить документ под новым именем (Ctrl+Shift+S)') + "\n" + \
                    "- " + self.tr('Выход') + ": " + self.tr('Закрыть программу (Ctrl+Q)') + "\n\n" + \
                    self.tr('Функции меню "Правка":') + '\n' + \
                    "- " + self.tr('Отменить') + ": Ctrl+Z\n" + \
                    "- " + self.tr('Повторить') + ": Ctrl+Y\n" + \
                    "- " + self.tr('Вырезать') + ": Ctrl+X\n" + \
                    "- " + self.tr('Копировать') + ": Ctrl+C\n" + \
                    "- " + self.tr('Вставить') + ": Ctrl+V\n" + \
                    "- " + self.tr('Удалить') + ": Del\n" + \
                    "- " + self.tr('Выделить все') + ": Ctrl+A\n\n" + \
                    self.tr('Функции меню "Вид":') + '\n' + \
                    "- " + self.tr('Увеличить/уменьшить шрифт редактора') + " (Ctrl+= / Ctrl+-)\n" + \
                    "- " + self.tr('Увеличить/уменьшить шрифт результатов') + " (Ctrl+Shift+= / Ctrl+Shift+-)\n\n" + \
                    self.tr('Функции меню "Пуск":') + '\n' + \
                    "- " + self.tr('Запуск анализатора') + ": F5\n\n" + \
                    self.tr('Дополнительно:') + '\n' + \
                    "- " + self.tr('Навигация по ошибкам: клик на ошибке в таблице') + "\n" + \
                    "- " + self.tr('Выделение ошибок: красное подчеркивание в тексте') + "\n"
        dlg = QDialog(self)
        dlg.setWindowTitle(self.tr('Справка'))
        dlg.resize(650, 550)
        dlg.setStyleSheet("""
            QDialog { background-color: #2b2b2b; }
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 2px solid #FFA500;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton {
                background-color: #FFA500;
                color: #000000;
                border: none;
                padding: 8px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #FFB52E; }
        """)
        lay = QVBoxLayout(dlg)
        te = QTextEdit()
        te.setReadOnly(True)
        te.setPlainText(help_text)
        btn = QPushButton(self.tr('Закрыть'))
        btn.clicked.connect(dlg.close)
        lay.addWidget(te)
        lay.addWidget(btn)
        dlg.exec()

    def show_about(self):
        QMessageBox.about(
            self,
            self.tr('О программе'),
            self.tr("Текстовый редактор с языковым процессором") + "\n\n" +
            self.tr("Версия: 3.0 (Scala Complex Automaton Parser)") + "\n\n" +
            self.tr("Автор: Васильев Антон Романович") + "\n" +
            self.tr("Вариант 8: Объявление комплексного числа в Scala") + "\n\n" +
            self.tr("(c) 2026")
        )

    def closeEvent(self, event):
        for i in range(self.editor_tabs.count()):
            tab = self.editor_tabs.widget(i)
            if tab.text_modified:
                reply = QMessageBox.question(
                    self, self.tr('Сохранение'),
                    self.tr('Есть несохраненные изменения. Закрыть программу?'),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    event.ignore()
                    return
        event.accept()


def main():
    suppress_console_output()
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(43, 43, 43))
    palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Base, QColor(30, 30, 30))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Button, QColor(64, 64, 64))
    palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Highlight, QColor(255, 165, 0))
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
    app.setPalette(palette)
    window = TextEditor()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()