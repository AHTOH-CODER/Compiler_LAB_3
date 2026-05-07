# Generated from ScalaComplex.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .ScalaComplexParser import ScalaComplexParser
else:
    from ScalaComplexParser import ScalaComplexParser

# This class defines a complete listener for a parse tree produced by ScalaComplexParser.
class ScalaComplexListener(ParseTreeListener):

    # Enter a parse tree produced by ScalaComplexParser#program.
    def enterProgram(self, ctx:ScalaComplexParser.ProgramContext):
        pass

    # Exit a parse tree produced by ScalaComplexParser#program.
    def exitProgram(self, ctx:ScalaComplexParser.ProgramContext):
        pass


    # Enter a parse tree produced by ScalaComplexParser#complexDecl.
    def enterComplexDecl(self, ctx:ScalaComplexParser.ComplexDeclContext):
        pass

    # Exit a parse tree produced by ScalaComplexParser#complexDecl.
    def exitComplexDecl(self, ctx:ScalaComplexParser.ComplexDeclContext):
        pass


    # Enter a parse tree produced by ScalaComplexParser#number.
    def enterNumber(self, ctx:ScalaComplexParser.NumberContext):
        pass

    # Exit a parse tree produced by ScalaComplexParser#number.
    def exitNumber(self, ctx:ScalaComplexParser.NumberContext):
        pass



del ScalaComplexParser