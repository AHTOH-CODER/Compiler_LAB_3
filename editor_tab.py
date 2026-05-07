from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPlainTextEdit, QTextEdit
from PyQt6.QtCore import Qt, QRect, QSize, QRegularExpression
from PyQt6.QtGui import (
    QPainter,
    QColor,
    QTextCursor,
    QTextFormat,
    QFont,
    QSyntaxHighlighter,
    QTextCharFormat,
)


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
        painter.fillRect(event.rect(), QColor(53, 53, 53))
        
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor(180, 180, 180))
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
            line_color = QColor(60, 60, 60)
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
        from main_window import TextEditor

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
            'if', 'else', 'elif', 'while', 'for', 'def', 'class', 'import',
            'from', 'return', 'True', 'False', 'None', 'and', 'or', 'not', 
            'int', 'float', 'str', 'print',
            # Ключевые слова Scala
            'val', 'var', 'new', 'Complex', 'object', 'trait', 'extends',
            'with', 'private', 'protected', 'override', 'implicit', 'lazy'
        ]
        
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor('#569CD6'))
        keyword_format.setFontWeight(QFont.Weight.Bold)
        
        for keyword in keywords:
            pattern = QRegularExpression(r'\b' + keyword + r'\b')
            rule = (pattern, keyword_format)
            self.highlighting_rules.append(rule)

        string_format = QTextCharFormat()
        string_format.setForeground(QColor('#CE9178'))
        pattern = QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"|\'[^\'\\]*(\\.[^\'\\]*)*\'')
        rule = (pattern, string_format)
        self.highlighting_rules.append(rule)

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor('#6A9955'))
        pattern = QRegularExpression(r'//.*|#.*')
        rule = (pattern, comment_format)
        self.highlighting_rules.append(rule)
        
        number_format = QTextCharFormat()
        number_format.setForeground(QColor('#B5CEA8'))
        # Поддержка целых, вещественных и мнимых чисел
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
        self.highlighter = SyntaxHighlighter(self.code_editor.document())
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