from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


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


class ErrorCollector:
    def __init__(self, lang: str = "ru"):
        self.errors: List[SyntaxErrorRecord] = []
        self.lang = lang

    def add(self, fragment: str, line: int, col: int, message: str):
        self.errors.append(SyntaxErrorRecord(
            fragment=fragment,
            line=line,
            col=col,
            message=message
        ))


class ANTLRParserAdapter:

    def __init__(self, code_text: str, lang: str = "ru"):
        self.code_text = code_text
        self.lang = lang if lang in ("ru", "en") else "ru"
        self.errors: List[SyntaxErrorRecord] = []

    def parse(self) -> ParseResult:
        self.errors = []

        if not self.code_text.strip():
            msg = "Empty input" if self.lang == "en" else "Пустой ввод"
            self.errors.append(SyntaxErrorRecord(
                fragment="EOF", line=1, col=1, message=msg
            ))
            return ParseResult(ok=False, errors=list(self.errors))

        collector = ErrorCollector(lang=self.lang)

        try:
            from antlr4 import InputStream, CommonTokenStream, Token
            from antlr_generated.ScalaComplexLexer import ScalaComplexLexer
            from antlr_generated.ScalaComplexParser import ScalaComplexParser

            input_stream = InputStream(self.code_text)

            lexer = ScalaComplexLexer(input_stream)

            lexer.removeErrorListeners()
            lexer_error_collector = LexerErrorListener(collector)
            lexer.addErrorListener(lexer_error_collector)

            token_stream = CommonTokenStream(lexer)
            token_stream.fill()

            parser = ScalaComplexParser(token_stream)
            parser.removeErrorListeners()
            parser_error_collector = ParserErrorListener(collector)
            parser.addErrorListener(parser_error_collector)

            parser.program()

            self.errors = collector.errors

        except ImportError as e:
            self.errors.append(SyntaxErrorRecord(
                fragment="IMPORT_ERROR",
                line=1,
                col=1,
                message=f"ANTLR not installed: {str(e)}"
            ))
        except Exception as e:
            self.errors.append(SyntaxErrorRecord(
                fragment="ERROR",
                line=1,
                col=1,
                message=f"Parse error: {str(e)}"
            ))

        return ParseResult(ok=len(self.errors) == 0, errors=list(self.errors))


class LexerErrorListener:
    def __init__(self, collector: ErrorCollector):
        self.collector = collector

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        fragment = offendingSymbol.text if offendingSymbol and offendingSymbol.text else "?"
        self.collector.add(
            fragment=fragment,
            line=line,
            col=column + 1,
            message=f"Lexical: {msg}"
        )


class ParserErrorListener:
    def __init__(self, collector: ErrorCollector):
        self.collector = collector

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        fragment = offendingSymbol.text if offendingSymbol and offendingSymbol.text else "EOF"
        if len(fragment) > 32:
            fragment = fragment[:29] + "..."
        self.collector.add(
            fragment=fragment,
            line=line,
            col=column + 1,
            message=f"Syntax: {msg}"
        )