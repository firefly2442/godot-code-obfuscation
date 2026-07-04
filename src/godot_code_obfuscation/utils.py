import random
import string
from lark import Token


def get_name_token(node):
    for child in node.children:
        if isinstance(child, Token) and child.type == "NAME":
            return child
    return None

def generate_name(n=18):
    return ''.join(random.choice(string.ascii_letters) for _ in range(n))


def apply_edits(source, edits):
    # sort backwards so offsets stay valid
    edits.sort(key=lambda x: x[0], reverse=True)

    for start, end, replacement in edits:
        source = source[:start] + replacement + source[end:]

    return source

def dump(node, indent=0):
    prefix = "  " * indent

    if isinstance(node, Tree):
        print(f"{prefix}{node.data}")
        for child in node.children:
            dump(child, indent + 1)
    else:
        print(f"{prefix}{node.type}: {node.value}")
