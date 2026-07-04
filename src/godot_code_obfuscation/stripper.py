from .utils import apply_edits


class CommentStripper:
    def __init__(self, source):
        self.source = source
        self.edits = []

    def strip(self):
        src = self.source
        i = 0
        n = len(src)

        in_string = False
        string_char = None
        triple = False

        while i < n:
            c = src[i]

            if not in_string:
                # beginning of string
                if c in ("'", '"'):
                    if src[i:i+3] == c * 3:
                        in_string = True
                        triple = True
                        string_char = c
                        i += 3
                        continue
                    else:
                        in_string = True
                        triple = False
                        string_char = c
                        i += 1
                        continue

                # comment
                if c == "#":
                    start = i

                    while i < n and src[i] != "\n":
                        i += 1

                    self.edits.append((start, i, ""))
                    continue

            else:
                if triple:
                    if src[i:i+3] == string_char * 3:
                        in_string = False
                        triple = False
                        i += 3
                        continue
                else:
                    if c == "\\":
                        i += 2
                        continue

                    if c == string_char:
                        in_string = False
                        i += 1
                        continue

            i += 1

        return apply_edits(src, self.edits)

class BlankLineStripper:
    def __init__(self, source):
        self.source = source

    def strip(self):
        lines = self.source.splitlines()

        # Keep only lines that contain something besides whitespace
        lines = [line for line in lines if line.strip()]

        return "\n".join(lines) + "\n"
