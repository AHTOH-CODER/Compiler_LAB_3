import re
from typing import List, Tuple, Optional, Dict, Any

class Token:
    pass
    CODES = {'KEYWORD': 1, 'IDENTIFIER': 2, 'INTEGER': 3, 'FLOAT': 4, 'IMAGINARY': 5, 'DELIMITER': 6, 'OPERATOR': 7, 'LPAREN': 8, 'RPAREN': 9, 'LBRACKET': 10, 'RBRACKET': 11, 'LBRACE': 12, 'RBRACE': 13, 'COMMA': 14, 'DOT': 15, 'COLON': 16, 'SEMICOLON': 17, 'COMMENT': 18, 'ERROR': 99}
    RU_TYPES = {'KEYWORD': 'КЛЮЧЕВОЕ СЛОВО', 'IDENTIFIER': 'ИДЕНТИФИКАТОР', 'INTEGER': 'ЦЕЛОЕ ЧИСЛО', 'FLOAT': 'ВЕЩЕСТВЕННОЕ ЧИСЛО', 'IMAGINARY': 'МНИМОЕ ЧИСЛО', 'DELIMITER': 'РАЗДЕЛИТЕЛЬ', 'OPERATOR': 'ОПЕРАТОР', 'LPAREN': 'ЛЕВАЯ СКОБКА', 'RPAREN': 'ПРАВАЯ СКОБКА', 'LBRACKET': 'ЛЕВАЯ КВАДРАТНАЯ СКОБКА', 'RBRACKET': 'ПРАВАЯ КВАДРАТНАЯ СКОБКА', 'LBRACE': 'ЛЕВАЯ ФИГУРНАЯ СКОБКА', 'RBRACE': 'ПРАВАЯ ФИГУРНАЯ СКОБКА', 'COMMA': 'ЗАПЯТАЯ', 'DOT': 'ТОЧКА', 'COLON': 'ДВОЕТОЧИЕ', 'SEMICOLON': 'ТОЧКА С ЗАПЯТОЙ', 'COMMENT': 'КОММЕНТАРИЙ', 'ERROR': 'ОШИБКА'}
    EN_TYPES = {'KEYWORD': 'KEYWORD', 'IDENTIFIER': 'IDENTIFIER', 'INTEGER': 'INTEGER', 'FLOAT': 'FLOAT', 'IMAGINARY': 'IMAGINARY', 'DELIMITER': 'DELIMITER', 'OPERATOR': 'OPERATOR', 'LPAREN': 'LEFT PAREN', 'RPAREN': 'RIGHT PAREN', 'LBRACKET': 'LEFT BRACKET', 'RBRACKET': 'RIGHT BRACKET', 'LBRACE': 'LEFT BRACE', 'RBRACE': 'RIGHT BRACE', 'COMMA': 'COMMA', 'DOT': 'DOT', 'COLON': 'COLON', 'SEMICOLON': 'SEMICOLON', 'COMMENT': 'COMMENT', 'ERROR': 'ERROR'}

    def __init__(self, token_type: str, value: str, line: int, start: int, end: int):
        self.token_type = token_type
        self.value = value
        self.line = line
        self.start = start
        self.end = end
        self.code = self.CODES.get(token_type, 99)

    def __repr__(self):
        return f"Token({self.token_type}, '{self.value}', line={self.line}, pos={self.start}-{self.end})"

    def get_display_type(self, lang='ru'):
        if lang == 'ru':
            return self.RU_TYPES.get(self.token_type, self.token_type)
        else:
            return self.EN_TYPES.get(self.token_type, self.token_type)

    def get_display_value(self, lang='ru'):
        if self.value == ' ':
            return '(пробел)' if lang == 'ru' else '(space)'
        elif self.value == '\n':
            return '\\n'
        elif self.value == '\t':
            return '\\t'
        return self.value

    def to_table_row(self, lang='ru') -> tuple:
        if lang == 'ru':
            location = f'строка {self.line}, {self.start}-{self.end}'
        else:
            location = f'line {self.line}, {self.start}-{self.end}'
        return (self.code, self.get_display_type(lang), self.get_display_value(lang), location)

class Scanner:
    pass
    KEYWORDS = {'val', 'Complex'}
    OPERATORS = {'=', '+', '-', '*', '/', '%', '==', '!=', '<', '>', '<=', '>='}
    SEPARATORS = {'(': 'LPAREN', ')': 'RPAREN', '[': 'LBRACKET', ']': 'RBRACKET', '{': 'LBRACE', '}': 'RBRACE', ',': 'COMMA', '.': 'DOT', ':': 'COLON', ';': 'SEMICOLON'}
    DELIMITERS = {' ', '\t', '\n'}

    def __init__(self):
        self.tokens: List[Token] = []
        self.errors: List[Token] = []
        self.line = 1
        self.pos = 1
        self.text = ''
        self.index = 0

    def analyze(self, text: str) -> Dict[str, Any]:
        pass
        self.tokens = []
        self.errors = []
        self.line = 1
        self.pos = 1
        self.index = 0
        self.text = text
        if not text:
            return {'tokens': [], 'errors': []}
        while self.index < len(self.text):
            ch = self.text[self.index]
            if ch in (' ', '\t'):
                self._handle_whitespace()
            elif ch == '\n':
                self._handle_newline()
            elif ch.isdigit():
                self._handle_number()
            elif ch.isalpha() or ch == '_':
                self._handle_identifier_or_keyword()
            elif ch in self.SEPARATORS:
                self._handle_special_char(ch)
            elif ch in '+-*/=<>':
                self._handle_operator()
            elif ch == '/' and self.index + 1 < len(self.text) and (self.text[self.index + 1] == '/'):
                self._handle_comment()
            else:
                self._handle_error(f"Недопустимый символ: '{ch}'")
        return {'tokens': self.tokens, 'errors': self.errors}

    def _handle_whitespace(self):
        pass
        start_pos = self.pos
        value = ''
        while self.index < len(self.text) and self.text[self.index] in (' ', '\t'):
            value += self.text[self.index]
            self._advance()
        token = Token('DELIMITER', value, self.line, start_pos, start_pos + len(value) - 1)
        self.tokens.append(token)

    def _handle_newline(self):
        pass
        token = Token('DELIMITER', '\n', self.line, self.pos, self.pos)
        self.tokens.append(token)
        self.line += 1
        self.pos = 1
        self.index += 1

    def _handle_number(self):
        pass
        start_pos = self.pos
        value = ''
        while self.index < len(self.text) and self.text[self.index].isdigit():
            value += self.text[self.index]
            self._advance()
        if self.index < len(self.text) and self.text[self.index] == '.':
            value += '.'
            self._advance()
            if self.index >= len(self.text) or not self.text[self.index].isdigit():
                self.tokens.append(Token('ERROR', value, self.line, start_pos, self.pos - 1))
                return
            while self.index < len(self.text) and self.text[self.index].isdigit():
                value += self.text[self.index]
                self._advance()
            if self.index < len(self.text) and self.text[self.index] == '.':
                while self.index < len(self.text) and (self.text[self.index].isdigit() or self.text[self.index] == '.'):
                    value += self.text[self.index]
                    self._advance()
                self.tokens.append(Token('ERROR', value, self.line, start_pos, self.pos - 1))
                return
            if self.index < len(self.text) and self.text[self.index] == 'i':
                value += 'i'
                self._advance()
                token = Token('IMAGINARY', value, self.line, start_pos, start_pos + len(value) - 1)
                self.tokens.append(token)
                return
            if self._is_malformed_number_continuation():
                self._consume_malformed_number(value, start_pos)
                return
            token = Token('FLOAT', value, self.line, start_pos, start_pos + len(value) - 1)
            self.tokens.append(token)
            return
        if self.index < len(self.text) and self.text[self.index] == 'i':
            value += 'i'
            self._advance()
            token = Token('IMAGINARY', value, self.line, start_pos, start_pos + len(value) - 1)
            self.tokens.append(token)
            return
        if self._is_malformed_number_continuation():
            self._consume_malformed_number(value, start_pos)
            return
        token = Token('INTEGER', value, self.line, start_pos, start_pos + len(value) - 1)
        self.tokens.append(token)

    def _is_malformed_number_continuation(self) -> bool:
        if self.index >= len(self.text):
            return False
        ch = self.text[self.index]
        if ch in self.DELIMITERS:
            return False
        if ch in self.SEPARATORS:
            return False
        if ch in '+-*/=<>':
            return False
        return True

    def _consume_malformed_number(self, value: str, start_pos: int):
        while self.index < len(self.text):
            ch = self.text[self.index]
            if ch in self.DELIMITERS or ch in self.SEPARATORS or ch in '+-*/=<>':
                break
            value += ch
            self._advance()
        self.tokens.append(Token('ERROR', value, self.line, start_pos, self.pos - 1))

    def _handle_identifier_or_keyword(self):
        pass
        start_pos = self.pos
        value = ''
        while self.index < len(self.text) and (self.text[self.index].isalnum() or self.text[self.index] == '_'):
            value += self.text[self.index]
            self._advance()
        malformed_value = value
        while self._has_malformed_identifier_bridge():
            malformed_value += self.text[self.index]
            self._advance()
            while self.index < len(self.text) and (self.text[self.index].isalnum() or self.text[self.index] == '_'):
                malformed_value += self.text[self.index]
                self._advance()
        if malformed_value != value:
            self.tokens.append(Token('ERROR', malformed_value, self.line, start_pos, self.pos - 1))
            return
        if value in self.KEYWORDS:
            token_type = 'KEYWORD'
        else:
            token_type = 'IDENTIFIER'
        token = Token(token_type, value, self.line, start_pos, start_pos + len(value) - 1)
        self.tokens.append(token)

    def _has_malformed_identifier_bridge(self) -> bool:
        if self.index + 1 >= len(self.text):
            return False
        bridge = self.text[self.index]
        next_ch = self.text[self.index + 1]
        if not (next_ch.isalpha() or next_ch == '_'):
            return False
        if bridge in self.DELIMITERS:
            return False
        return not (bridge.isalnum() or bridge == '_')

    def _handle_operator(self):
        pass
        start_pos = self.pos
        ch = self.text[self.index]
        if ch in '=!<>' and self.index + 1 < len(self.text) and (self.text[self.index + 1] == '='):
            op = ch + '='
            self._advance()
            self._advance()
        else:
            op = ch
            self._advance()
        if op in self.OPERATORS:
            token = Token('OPERATOR', op, self.line, start_pos, start_pos + len(op) - 1)
            self.tokens.append(token)
        else:
            self._add_error(f"Недопустимый оператор: '{op}'", self.line, start_pos, start_pos + len(op) - 1)

    def _handle_special_char(self, ch):
        pass
        if ch == '.' and self.index + 1 < len(self.text) and self.text[self.index + 1].isdigit():
            start_pos = self.pos
            value = '.'
            self._advance()
            while self.index < len(self.text) and self.text[self.index].isdigit():
                value += self.text[self.index]
                self._advance()
            if self._is_malformed_number_continuation():
                self._consume_malformed_number(value, start_pos)
            else:
                self.tokens.append(Token('ERROR', value, self.line, start_pos, self.pos - 1))
            return
        token_type = self.SEPARATORS[ch]
        token = Token(token_type, ch, self.line, self.pos, self.pos)
        self.tokens.append(token)
        self._advance()

    def _handle_comment(self):
        pass
        start_pos = self.pos
        value = ''
        while self.index < len(self.text) and self.text[self.index] != '\n':
            value += self.text[self.index]
            self._advance()
        token = Token('COMMENT', value, self.line, start_pos, start_pos + len(value) - 1)
        self.tokens.append(token)

    def _handle_error(self, message: str):
        pass
        self.tokens.append(Token('ERROR', message, self.line, self.pos, self.pos))
        self._advance()

    def _add_error(self, message: str, line: int, start: int, end: int):
        pass
        token = Token('ERROR', message, line, start, end)
        self.errors.append(token)
        self.tokens.append(token)

    def _advance(self):
        pass
        self.index += 1
        self.pos += 1

    def get_token_table_data(self, lang='ru') -> List[tuple]:
        return [token.to_table_row(lang) for token in self.tokens]

    def get_errors_table_data(self, lang='ru') -> List[tuple]:
        return [token.to_table_row(lang) for token in self.errors]
if __name__ == '__main__':
    scanner = Scanner()
    test_code = 'val c1: Complex = new Complex(1.0, 2.0)'
    results = scanner.analyze(test_code)
    print('Токены:')
    for t in results['tokens']:
        print(t.to_table_row('ru'))
    print('\nОшибки:')
    for e in results['errors']:
        print(e.to_table_row('ru'))
