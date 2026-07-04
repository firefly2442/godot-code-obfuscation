from lark import Tree, Token

class Visitor:
    def visit(self, node):
        if isinstance(node, Tree):
            method = getattr(self, f"visit_{node.data}", self.generic_visit)
            return method(node)

        elif isinstance(node, Token):
            return self.visit_token(node)

    def visit_token(self, token):
        pass

    def generic_visit(self, node):
        for child in node.children:
            self.visit(child)