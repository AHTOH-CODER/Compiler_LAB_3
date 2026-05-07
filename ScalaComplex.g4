grammar ScalaComplex;

options { language=Python3; }

program
    : (complexDecl NL*)* EOF
    ;

complexDecl
    : VAL ID ASSIGN COMPLEX LPAREN number COMMA number RPAREN SEMI
    ;

number
    : INTEGER
    | FLOAT
    ;

VAL       : 'val' ;
COMPLEX   : 'Complex' ;

ASSIGN    : '=' ;
LPAREN    : '(' ;
RPAREN    : ')' ;
COMMA     : ',' ;
SEMI      : ';' ;

INTEGER   : '-'? [0-9]+ ;
FLOAT     : '-'? [0-9]+ '.' [0-9]+ ;

ID        : [a-zA-Z_] [a-zA-Z0-9_]* ;

NL        : '\r'? '\n' ;
WS        : [ \t]+ -> skip ;
COMMENT   : '//' ~[\r\n]* -> skip ;
