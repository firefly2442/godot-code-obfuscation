# https://github.com/Scony/godot-gdscript-toolkit
from gdtoolkit.parser import parser
from gdtoolkit.formatter import format_code
import argparse
from pathlib import Path
import string
import random
from lark import Tree, Token
from dataclasses import dataclass
import re



def parse_args():
    parser = argparse.ArgumentParser(
        description="Obfuscate GDScript (.gd) file or directory contents, renaming identifiers and stripping comments."
    )
    parser.add_argument(
        "input_path",
        help="Path to a .gd file or a directory containing GDScript files."
    )
    parser.add_argument(
        "-l", "--name-length",
        type=int,
        default=12,
        help="Length of generated obfuscated identifier names (default: 12)."
    )
    parser.add_argument(
        "-e", "--exclude",
        nargs="+",
        default=[],
        metavar="FILE",
        help="One or more filenames to exclude (example: -e UID.gd Player.gd)."
    )

    args = parser.parse_args()

    # Cleanup input path (strip stray quotes, same as original behavior)
    args.input_path = args.input_path.replace("'", "").replace('"', "")

    return args

@dataclass
class Symbol:
    name: str
    token: Token
    kind: str
    new_name: str | None = None

class Scope:
    def __init__(self, parent=None):
        self.parent = parent
        self.symbols = {}

    def define(self, symbol):
        symbol.new_name = generate_name()
        self.symbols[symbol.name] = symbol

    def lookup(self, name):
        scope = self
        while scope:
            if name in scope.symbols:
                return scope.symbols[name]
            scope = scope.parent
        return None
    

class Visitor:
    def visit(self, node):
        if isinstance(node, Tree):
            method = getattr(self, f"visit_{node.data}", self.generic_visit)
            return method(node)

    def generic_visit(self, node):
        for child in node.children:
            self.visit(child)

class DebugVisitor(Visitor):
    WATCH = {
        "func_def",
        "func_header",
        "func_arg",
        "func_arg_typed",
        "func_var_assgnd",
        "func_var_typed_assgnd",
        "var_stmt",
    }

    def generic_visit(self, node):
        if node.data in self.WATCH:
            print(f"\n=== {node.data} ===")

            for i, child in enumerate(node.children):
                if isinstance(child, Tree):
                    print(f"  [{i}] Tree({child.data})")
                else:
                    print(f"  [{i}] Token({child.type}, {child.value})")

        super().generic_visit(node)

class Renamer(Visitor):
    def __init__(self, global_scope):
        self.scope = global_scope
        self.edits = []

    def visit_func_def(self, node):
        old_scope = self.scope
        self.scope = node.scope
        self.generic_visit(node)
        self.scope = old_scope

    def visit_func_var_typed_assgnd(self, node):
        name_token = node.children[0]

        symbol = self.scope.lookup(name_token.value)
        if symbol:
            meta = node.meta

            if isinstance(name_token, Token) and name_token.type == "NAME":
                self.edits.append(
                    (name_token.start_pos, name_token.end_pos, generate_name())
                )

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
            kind="param"
        ))

    def visit_func_var_typed_assgnd(self, node):
        child = node.children[0]

        if isinstance(child, Token) and child.type == "NAME":
            name = child.value

            self.scope.define(Symbol(
                name=name,
                token=child,
                kind="local"
            ))


def get_name_token(node):
    for child in node.children:
        if isinstance(child, Token) and child.type == "NAME":
            return child
    return None

def generate_name(n=12):
    return ''.join(random.choice(string.ascii_letters) for _ in range(n))

def build_rename_map(names, length=12):
    return {name: generate_name(length) for name in names}

def collect_local_variables(tree):
    locals_set = set()

    def walk(node):
        if isinstance(node, Tree):
            if node.data == "func_var_typed_assgnd":
                name_token = node.children[0]
                if isinstance(name_token, Token) and name_token.type == "NAME":
                    locals_set.add(name_token.value)

            for child in node.children:
                walk(child)

    walk(tree)
    return locals_set

def obfuscate_tokens(tree, rename_map):
    def walk(node, in_func_header=False):

        if isinstance(node, Tree):

            if node.data == "func_header":
                in_func_header = True

            for c in node.children:
                walk(c, in_func_header)

        elif isinstance(node, Token):
            # ONLY rename identifiers
            if node.type == "NAME":
                if not in_func_header:
                    if node.value in rename_map:
                        node.value = rename_map[node.value]

        return node

    return walk(tree)


def replace_tokens(node, rename_map):
    if isinstance(node, Tree):
        node.children = [replace_tokens(c, rename_map) for c in node.children]
        return node

    if isinstance(node, Token) and node.type == "NAME":
        if node.value in rename_map:
            return Token(node.type, rename_map[node.value])

    return node

def dump(node, indent=0):
    prefix = "  " * indent

    if isinstance(node, Tree):
        print(f"{prefix}{node.data}")
        for child in node.children:
            dump(child, indent + 1)
    else:
        print(f"{prefix}{node.type}: {node.value}")


def apply_edits(source, edits):
    # sort backwards so offsets stay valid
    edits.sort(key=lambda x: x[0], reverse=True)

    for start, end, replacement in edits:
        source = source[:start] + replacement + source[end:]

    return source

def main():
    args = parse_args()

    input_path = Path(args.input_path)
    name_length = args.name_length
    excluded_files = set(args.exclude)

    for file_path in input_path.rglob("*.gd"):
        try:
            if file_path.name in excluded_files:
                print(f"Skipping excluded file: {file_path.name}")
                continue

            if file_path.name != "custom_tree_tooltip.gd":
                continue

            print(f"Reading: {file_path.name}")
            content = file_path.read_text(encoding="utf-8")

            tree = parser.parse(content, gather_metadata=True)
            debug = DebugVisitor()
            debug.visit(tree)

            collector = SymbolCollector()
            collector.visit(tree)

            renamer = Renamer(collector.global_scope)
            renamer.visit(tree)

            new_source = apply_edits(content, renamer.edits)

            print(new_source)

            file_path.write_text(new_source, encoding="utf-8")
            
            
        except Exception as e:
            print(f"Error reading: {file_path}: {e}")


if __name__ == "__main__":
    main()
