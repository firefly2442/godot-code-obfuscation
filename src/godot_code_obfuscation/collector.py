from .visitor import Visitor
from .symbols import Scope, Symbol
from lark import Token



class SymbolCollector(Visitor):
    def __init__(self):
        self.global_scope = Scope()
        self.scope = self.global_scope

    def visit_func_def(self, node):
        old_scope = self.scope
        self.scope = Scope(parent=old_scope)

        node.scope = self.scope  # store for renamer

        self.generic_visit(node)

        self.scope = old_scope

    def visit_func_arg_typed(self, node):
        name = node.children[0].value

        self.scope.define(Symbol(
            name=name,
            token=node.children[0],
            kind="param",
            scope=self.scope,
        ))

    def visit_func_var_typed_assgnd(self, node):
        child = node.children[0]

        if isinstance(child, Token) and child.type == "NAME":
            name = child.value

            self.scope.define(Symbol(
                name=name,
                token=child,
                kind="local",
                scope=self.scope,
            ))