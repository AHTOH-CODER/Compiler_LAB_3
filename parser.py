from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from scanner import Token


@dataclass
class SyntaxErrorRecord:
    fragment: str
    line: int
    col: int
    message: str

    def location_ru(self) -> str:
        return f"строка {self.line}, позиция {self.col}"

    def location_en(self) -> str:
        return f"line {self.line}, position {self.col}"


@dataclass
class ParseResult:
    ok: bool
    errors: List[SyntaxErrorRecord] = field(default_factory=list)


class Parser:
    def __init__(self, tokens: List["Token"], lang: str = "ru"):
        self.tokens = self._filter_tokens(tokens)
        self.pos = 0
        self.errors: List[SyntaxErrorRecord] = []
        self.lang = lang if lang in ("ru", "en") else "ru"
        self.current_line = 1

    def _m(self, ru: str, en: str) -> str:
        return en if self.lang == "en" else ru

    @staticmethod
    def _filter_tokens(tokens: List["Token"]) -> List["Token"]:
        out = []
        for t in tokens:
            if t.token_type in ('DELIMITER', 'COMMENT'):
                continue
            out.append(t)
        return out

    def _current(self) -> Optional["Token"]:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _advance(self):
        if self._current():
            self.current_line = self._current().line
        self.pos += 1

    def _fragment(self, t: Optional["Token"]) -> str:
        if not t:
            return "EOF"
        raw = getattr(t, "raw_lexeme", t.value)
        return raw if len(raw) <= 32 else raw[:29] + "..."

    def _add_error(self, fragment: str, line: int, col: int, message: str):
        self.errors.append(SyntaxErrorRecord(fragment=fragment, line=line, col=col, message=message))

    def _check_value(self, value: str) -> bool:
        t = self._current()
        return t is not None and t.value == value

    def _is_keyword(self, word: str) -> bool:
        t = self._current()
        return t is not None and t.token_type == "KEYWORD" and t.value == word

    def _is_identifier(self) -> bool:
        t = self._current()
        return t is not None and t.token_type == "IDENTIFIER"

    def _is_number(self) -> bool:
        t = self._current()
        return t is not None and t.token_type in ("INTEGER", "FLOAT")

    def _report_current_error(self, message: str):
        t = self._current()
        if t is None:
            self._add_error("EOF", self.current_line, 1, message)
            return
        self._add_error(self._fragment(t), t.line, t.start, message)

    def parse(self) -> ParseResult:
        self.errors = []
        self.pos = 0
        self.current_line = 1

        if not self.tokens:
            self._add_error("EOF", 1, 1, self._m("Пустой ввод", "Empty input"))
            return ParseResult(ok=False, errors=list(self.errors))

        while self._current() is not None:
            if (
                self.pos > 0
                and self.tokens[self.pos - 1].value == ";"
                and self._current().token_type == "ERROR"
            ):
                self._report_current_error(self._m(
                    "Некорректный фрагмент после завершенного объявления",
                    "Invalid fragment after completed declaration",
                ))
                self._advance()
                continue
            self._parse_complex_declaration()

        return ParseResult(ok=len(self.errors) == 0, errors=list(self.errors))

    def _sync_to_semicolon_or_eof(self, expect_semicolon: bool = False):
        found_semicolon = False
        while self._current() is not None and not self._check_value(";"):
            self._advance()
        if self._check_value(";"):
            found_semicolon = True
            self._advance()
        if expect_semicolon and not found_semicolon:
            last = self.tokens[-1] if self.tokens else None
            if last is None:
                self._add_error(
                    "EOF",
                    self.current_line,
                    1,
                    self._m("Ожидалась ';' в конце объявления", "Expected ';' at end of declaration"),
                )
            else:
                self._add_error(
                    "EOF",
                    last.line,
                    last.end + 1,
                    self._m("Ожидалась ';' в конце объявления", "Expected ';' at end of declaration"),
                )

    def _sync_after_declaration_error(self, expect_semicolon: bool = False):
        # После первой ошибки в объявлении доходим до конца текущей конструкции,
        # затем пропускаем «хвост», пока не встретим следующее корректное начало `val`.
        self._sync_to_semicolon_or_eof(expect_semicolon=expect_semicolon)
        while self._current() is not None and not self._is_keyword("val"):
            self._advance()

    def _recover_to_identifier_before_assign(self):
        """
        Восстановление после ошибки в начале объявления.
        Ищем идентификатор переменной перед '='.
        """
        idx = self.pos + 1
        while idx < len(self.tokens):
            tok = self.tokens[idx]
            if tok.value == ";":
                return
            if tok.token_type == "IDENTIFIER":
                self.pos = idx
                return
            idx += 1

    def _recover_to_lparen_or_semicolon(self):
        while self._current() is not None and not (self._check_value("(") or self._check_value(";")):
            self._advance()

    def _recover_to_any(self, values: set[str]):
        while self._current() is not None and self._current().value not in values:
            self._advance()

    def _recover_to_assign_or_semicolon(self):
        self._recover_to_any({"=", ";"})

    def _recover_to_complex_or_lparen_or_semicolon(self) -> int:
        skipped = 0
        while self._current() is not None:
            if self._check_value(";") or self._check_value("("):
                return skipped
            if self._is_keyword("Complex"):
                return skipped
            self._advance()
            skipped += 1
        return skipped

    def _expect_keyword(self, word: str, message_ru: str, message_en: str) -> bool:
        if self._is_keyword(word):
            self._advance()
            return True
        self._report_current_error(self._m(message_ru, message_en))
        return False

    def _expect_identifier(self) -> bool:
        if self._is_identifier():
            self._advance()
            return True
        self._report_current_error(self._m(
            "Ожидался идентификатор",
            "Expected identifier",
        ))
        return False

    def _expect_value(self, value: str, message_ru: str, message_en: str) -> bool:
        if self._check_value(value):
            self._advance()
            return True
        self._report_current_error(self._m(message_ru, message_en))
        return False

    def _expect_number(self, which_ru: str, which_en: str) -> bool:
        if self._is_number():
            self._advance()
            return True
        self._report_current_error(self._m(
            f"Ожидалось число ({which_ru})",
            f"Expected number ({which_en})",
        ))
        return False

    def _parse_complex_declaration(self):
        """
        Принимаем только конструкцию:
          val <id> = Complex(<num>, <num>);
        Нейтрализация ошибок: при первой ошибке синхронизируемся до ';' и продолжаем.
        """
        start_errors = len(self.errors)

        if not self._expect_keyword(
            "val",
            "Ожидалось ключевое слово 'val'",
            "Expected keyword 'val'",
        ):
            self._recover_to_identifier_before_assign()

        if not self._expect_identifier():
            # Даже при ошибке в имени переменной стараемся продолжить и проверить
            # правую часть объявления, чтобы не терять ошибки аргументов.
            self._recover_to_assign_or_semicolon()
            if self._check_value(";") or self._current() is None:
                self._sync_after_declaration_error(expect_semicolon=True)
                return

        if not self._expect_value(
            "=",
            "Ожидался оператор '='",
            "Expected '=' operator",
        ):
            current = self._current()
            op_fragment = None
            op_line = None
            op_col = None
            if (
                current is not None
                and current.token_type == "ERROR"
                and self.pos + 2 < len(self.tokens)
                and self.tokens[self.pos + 1].token_type == "OPERATOR"
                and self.tokens[self.pos + 2].token_type == "OPERATOR"
            ):
                op_fragment = self.tokens[self.pos + 1].value + self.tokens[self.pos + 2].value
                op_line = self.tokens[self.pos + 1].line
                op_col = self.tokens[self.pos + 1].start
            skipped = self._recover_to_complex_or_lparen_or_semicolon()
            if op_fragment is not None:
                self._add_error(
                    op_fragment,
                    op_line,
                    op_col,
                    self._m("Некорректная запись оператора присваивания", "Invalid assignment operator"),
                )
            elif (
                current is not None
                and current.token_type == "ERROR"
                and skipped >= 2
                and self.pos > 0
                and self.tokens[self.pos - 1].token_type == "OPERATOR"
                and self.tokens[self.pos - 1].value != "="
            ):
                self._add_error(
                    self._fragment(current),
                    current.line,
                    current.start,
                    self._m("Некорректная запись оператора присваивания", "Invalid assignment operator"),
                )
            if self._check_value(";") or self._current() is None:
                self._sync_after_declaration_error(expect_semicolon=True)
                return

        # Для ошибки в имени конструктора (Comple вместо Complex) должен
        # формироваться ровно один диагноз по данному объявлению.
        if not self._is_keyword("Complex"):
            self._report_current_error(self._m(
                "Ожидалось ключевое слово 'Complex'",
                "Expected keyword 'Complex'",
            ))
            self._recover_to_lparen_or_semicolon()
            if self._check_value("("):
                self._advance()
            else:
                self._sync_after_declaration_error(expect_semicolon=True)
                return
        else:
            self._advance()

        if self.pos > 0 and self.tokens[self.pos - 1].value != "(":
            if not self._expect_value(
                "(",
                "Ожидалась '(' после 'Complex'",
                "Expected '(' after 'Complex'",
            ):
                self._sync_after_declaration_error(expect_semicolon=True)
                return

        first_ok = self._expect_number("первый аргумент", "first argument")
        if not first_ok:
            # После ошибки первого аргумента ищем реальную границу списка
            # аргументов (',' или ')'), а не ';', чтобы не создавать
            # лишний диагноз "ожидалась ','".
            self._recover_to_any({",", ")"})
            if self._check_value(")"):
                # Пустой/битый первый аргумент: считаем это одной ошибкой
                # и, если дальше есть еще одна '(', продолжаем проверку
                # следующего списка аргументов (Complex()(...)).
                self._advance()
                if self._check_value("("):
                    self._advance()
                    first_ok = self._expect_number("первый аргумент", "first argument")
                    if not first_ok:
                        self._sync_after_declaration_error(expect_semicolon=True)
                        return
                else:
                    self._sync_after_declaration_error(expect_semicolon=True)
                    return

        comma_ok = self._expect_value(
            ",",
            "Ожидалась ',' между аргументами",
            "Expected ',' between arguments",
        )
        if not comma_ok:
            self._sync_after_declaration_error(expect_semicolon=True)
            return

        second_ok = self._expect_number("второй аргумент", "second argument")
        if not second_ok:
            # Для второго аргумента не плодим каскад: после одной ошибки
            # доходим до ')' и завершаем объявление.
            self._recover_to_any({")"})
            if not self._check_value(")"):
                self._sync_after_declaration_error(expect_semicolon=True)
                return

        if not self._expect_value(
            ")",
            "Ожидалась ')' после аргументов",
            "Expected ')' after arguments",
        ):
            self._recover_to_any({")", ";"})
            if self._check_value(")"):
                self._advance()
            else:
                self._sync_after_declaration_error(expect_semicolon=True)
                return

        self._expect_value(
            ";",
            "Ожидалась ';' в конце объявления",
            "Expected ';' at end of declaration",
        )

        # Если были ошибки — синхронизируемся до конца текущего объявления.
        if len(self.errors) != start_errors:
            self._sync_after_declaration_error()