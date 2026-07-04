from dataclasses import dataclass
from lark import Token
from .utils import generate_name


@dataclass
class Symbol:
    name: str
    token: Token
    kind: str # local, parameter, member, function...
    scope: "Scope"

    new_name: str | None = None

    references: list[Token] = None

    def __post_init__(self):
        if self.references is None:
            self.references = []

class Scope:
    def __init__(self, parent=None):
        self.parent = parent
        self.symbols = {}

    def define(self, symbol):
        symbol.new_name = generate_name()
        self.symbols[symbol.name] = symbol
        
        # print(f"DEFINE {symbol.kind}: {symbol.name} -> {symbol.new_name}")

    def lookup(self, name):
        scope = self
        while scope:
            if name in scope.symbols:
                return scope.symbols[name]
            scope = scope.parent
        return None
    