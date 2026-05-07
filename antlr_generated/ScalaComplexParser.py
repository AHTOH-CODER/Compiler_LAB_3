# Generated from ScalaComplex.g4 by ANTLR 4.13.2
# encoding: utf-8
from antlr4 import *
from io import StringIO
import sys
if sys.version_info[1] > 5:
	from typing import TextIO
else:
	from typing.io import TextIO

def serializedATN():
    return [
        4,1,13,34,2,0,7,0,2,1,7,1,2,2,7,2,1,0,1,0,5,0,9,8,0,10,0,12,0,12,
        9,0,5,0,14,8,0,10,0,12,0,17,9,0,1,0,1,0,1,1,1,1,1,1,1,1,1,1,1,1,
        1,1,1,1,1,1,1,1,1,1,1,2,1,2,1,2,0,0,3,0,2,4,0,1,1,0,8,9,32,0,15,
        1,0,0,0,2,20,1,0,0,0,4,31,1,0,0,0,6,10,3,2,1,0,7,9,5,11,0,0,8,7,
        1,0,0,0,9,12,1,0,0,0,10,8,1,0,0,0,10,11,1,0,0,0,11,14,1,0,0,0,12,
        10,1,0,0,0,13,6,1,0,0,0,14,17,1,0,0,0,15,13,1,0,0,0,15,16,1,0,0,
        0,16,18,1,0,0,0,17,15,1,0,0,0,18,19,5,0,0,1,19,1,1,0,0,0,20,21,5,
        1,0,0,21,22,5,10,0,0,22,23,5,3,0,0,23,24,5,2,0,0,24,25,5,4,0,0,25,
        26,3,4,2,0,26,27,5,6,0,0,27,28,3,4,2,0,28,29,5,5,0,0,29,30,5,7,0,
        0,30,3,1,0,0,0,31,32,7,0,0,0,32,5,1,0,0,0,2,10,15
    ]

class ScalaComplexParser ( Parser ):

    grammarFileName = "ScalaComplex.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "'val'", "'Complex'", "'='", "'('", "')'", 
                     "','", "';'" ]

    symbolicNames = [ "<INVALID>", "VAL", "COMPLEX", "ASSIGN", "LPAREN", 
                      "RPAREN", "COMMA", "SEMI", "INTEGER", "FLOAT", "ID", 
                      "NL", "WS", "COMMENT" ]

    RULE_program = 0
    RULE_complexDecl = 1
    RULE_number = 2

    ruleNames =  [ "program", "complexDecl", "number" ]

    EOF = Token.EOF
    VAL=1
    COMPLEX=2
    ASSIGN=3
    LPAREN=4
    RPAREN=5
    COMMA=6
    SEMI=7
    INTEGER=8
    FLOAT=9
    ID=10
    NL=11
    WS=12
    COMMENT=13

    def __init__(self, input:TokenStream, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.13.2")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None




    class ProgramContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def EOF(self):
            return self.getToken(ScalaComplexParser.EOF, 0)

        def complexDecl(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(ScalaComplexParser.ComplexDeclContext)
            else:
                return self.getTypedRuleContext(ScalaComplexParser.ComplexDeclContext,i)


        def NL(self, i:int=None):
            if i is None:
                return self.getTokens(ScalaComplexParser.NL)
            else:
                return self.getToken(ScalaComplexParser.NL, i)

        def getRuleIndex(self):
            return ScalaComplexParser.RULE_program

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterProgram" ):
                listener.enterProgram(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitProgram" ):
                listener.exitProgram(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitProgram" ):
                return visitor.visitProgram(self)
            else:
                return visitor.visitChildren(self)




    def program(self):

        localctx = ScalaComplexParser.ProgramContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_program)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 15
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==1:
                self.state = 6
                self.complexDecl()
                self.state = 10
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                while _la==11:
                    self.state = 7
                    self.match(ScalaComplexParser.NL)
                    self.state = 12
                    self._errHandler.sync(self)
                    _la = self._input.LA(1)

                self.state = 17
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 18
            self.match(ScalaComplexParser.EOF)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ComplexDeclContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def VAL(self):
            return self.getToken(ScalaComplexParser.VAL, 0)

        def ID(self):
            return self.getToken(ScalaComplexParser.ID, 0)

        def ASSIGN(self):
            return self.getToken(ScalaComplexParser.ASSIGN, 0)

        def COMPLEX(self):
            return self.getToken(ScalaComplexParser.COMPLEX, 0)

        def LPAREN(self):
            return self.getToken(ScalaComplexParser.LPAREN, 0)

        def number(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(ScalaComplexParser.NumberContext)
            else:
                return self.getTypedRuleContext(ScalaComplexParser.NumberContext,i)


        def COMMA(self):
            return self.getToken(ScalaComplexParser.COMMA, 0)

        def RPAREN(self):
            return self.getToken(ScalaComplexParser.RPAREN, 0)

        def SEMI(self):
            return self.getToken(ScalaComplexParser.SEMI, 0)

        def getRuleIndex(self):
            return ScalaComplexParser.RULE_complexDecl

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterComplexDecl" ):
                listener.enterComplexDecl(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitComplexDecl" ):
                listener.exitComplexDecl(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitComplexDecl" ):
                return visitor.visitComplexDecl(self)
            else:
                return visitor.visitChildren(self)




    def complexDecl(self):

        localctx = ScalaComplexParser.ComplexDeclContext(self, self._ctx, self.state)
        self.enterRule(localctx, 2, self.RULE_complexDecl)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 20
            self.match(ScalaComplexParser.VAL)
            self.state = 21
            self.match(ScalaComplexParser.ID)
            self.state = 22
            self.match(ScalaComplexParser.ASSIGN)
            self.state = 23
            self.match(ScalaComplexParser.COMPLEX)
            self.state = 24
            self.match(ScalaComplexParser.LPAREN)
            self.state = 25
            self.number()
            self.state = 26
            self.match(ScalaComplexParser.COMMA)
            self.state = 27
            self.number()
            self.state = 28
            self.match(ScalaComplexParser.RPAREN)
            self.state = 29
            self.match(ScalaComplexParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class NumberContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def INTEGER(self):
            return self.getToken(ScalaComplexParser.INTEGER, 0)

        def FLOAT(self):
            return self.getToken(ScalaComplexParser.FLOAT, 0)

        def getRuleIndex(self):
            return ScalaComplexParser.RULE_number

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterNumber" ):
                listener.enterNumber(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitNumber" ):
                listener.exitNumber(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitNumber" ):
                return visitor.visitNumber(self)
            else:
                return visitor.visitChildren(self)




    def number(self):

        localctx = ScalaComplexParser.NumberContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_number)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 31
            _la = self._input.LA(1)
            if not(_la==8 or _la==9):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx





