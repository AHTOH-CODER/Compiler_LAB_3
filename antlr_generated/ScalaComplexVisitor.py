# Generated from ScalaComplex.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .ScalaComplexParser import ScalaComplexParser
else:
    from ScalaComplexParser import ScalaComplexParser

# This class defines a complete generic visitor for a parse tree produced by ScalaComplexParser.

class ScalaComplexVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by ScalaComplexParser#program.
    def visitProgram(self, ctx:ScalaComplexParser.ProgramContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ScalaComplexParser#complexDecl.
    def visitComplexDecl(self, ctx:ScalaComplexParser.ComplexDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ScalaComplexParser#number.
    def visitNumber(self, ctx:ScalaComplexParser.NumberContext):
        return self.visitChildren(ctx)



del ScalaComplexParser