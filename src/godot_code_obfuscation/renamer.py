from .visitor import Visitor


class Renamer(Visitor):
    def __init__(self, global_scope, source):
        self.scope = global_scope
        self.source = source
        self.edits = []

    def visit_func_def(self, node):
        old_scope = self.scope
        self.scope = node.scope
        self.generic_visit(node)
        self.scope = old_scope

    def visit_token(self, token):
        if token.type != "NAME":
            return

        # Don't rename properties after '.'
        if token.start_pos > 0 and self.source[token.start_pos - 1] == ".":
            return

        symbol = self.scope.lookup(token.value)

        if symbol:
            self.edits.append(
                (
                    token.start_pos,
                    token.end_pos,
                    symbol.new_name,
                )
            )