KEYWORDS = ("fn", "return", "let", "const")
BASE = ("+", "-", "*", "/", "=", "<", ">", "!", "%", "|", "&", "^", "~")
SPECIAL = ("->", "=")
GENERAL_OPERATORS = ("+", "-", "*", "/", "%", "|", "&", "^")
UNARY_OPERATORS = ("~", "!")
ASSIGN_OPERATORS = ("+=", "-=", "*=", "/=", "%=", "|=", "&=", "^=", "~=")
CONDITION_OPERATORS = ("<", ">", "<=", ">=", "!=", "&&", "||", "^^")
OPERATORS = SPECIAL + GENERAL_OPERATORS + UNARY_OPERATORS + ASSIGN_OPERATORS + CONDITION_OPERATORS