"""Remove all Chinese comments and docstrings from Python source files."""

import ast
import io
import re
import sys
import tokenize
from pathlib import Path

CHINESE_RE = re.compile(r"[一-鿿㐀-䶿豈-﫿　-〿＀-￯⺀-⻿]")


def has_chinese(text: str) -> bool:
    return bool(CHINESE_RE.search(text))


def get_chinese_docstring_info(source: str) -> dict[int, dict]:
    """
    Returns a dict keyed by start line number of Chinese docstrings.
    Value: {start, end, col_offset, only_stmt} where only_stmt means
    it's the sole statement in its block (needs 'pass' replacement).
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}

    result = {}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if not node.body:
            continue
        first = node.body[0]
        if not (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
            and has_chinese(first.value.value)
        ):
            continue
        only_stmt = len(node.body) == 1 and not isinstance(node, ast.Module)
        result[first.lineno] = {
            "start": first.lineno,
            "end": first.end_lineno,
            "col_offset": first.col_offset,
            "only_stmt": only_stmt,
        }
    return result


def process_file(path: Path) -> tuple[bool, str]:
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines(keepends=True)

    docstrings = get_chinese_docstring_info(source)

    # Collect lines covered by Chinese docstrings
    docstring_lines: set[int] = set()
    pass_replacements: dict[int, str] = {}  # line_no -> replacement line

    for info in docstrings.values():
        for ln in range(info["start"], info["end"] + 1):
            docstring_lines.add(ln)
        if info["only_stmt"]:
            # Replace first line with 'pass' at correct indentation
            indent = " " * info["col_offset"]
            pass_replacements[info["start"]] = f"{indent}pass\n"

    # Find comment tokens with Chinese
    comment_remove: set[int] = set()   # full line removal
    comment_inline: dict[int, int] = {}  # line_no -> col start

    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except tokenize.TokenError:
        return False, source

    for tok_type, tok_string, tok_start, *_ in tokens:
        if tok_type != tokenize.COMMENT or not has_chinese(tok_string):
            continue
        line_no, col = tok_start
        before = lines[line_no - 1][:col]
        if before.strip() == "":
            comment_remove.add(line_no)
        else:
            comment_inline[line_no] = col

    # Build new lines
    new_lines: list[str] = []
    for i, line in enumerate(lines, start=1):
        if i in docstring_lines:
            if i in pass_replacements:
                new_lines.append(pass_replacements[i])
            # else: skip line
        elif i in comment_remove:
            pass  # skip
        elif i in comment_inline:
            col = comment_inline[i]
            new_lines.append(line[:col].rstrip() + "\n")
        else:
            new_lines.append(line)

    new_source = "".join(new_lines)
    return new_source != source, new_source


def main(roots: list[Path]) -> None:
    py_files: list[Path] = []
    for root in roots:
        py_files.extend(root.rglob("*.py"))

    changed = 0
    errors = 0
    for path in sorted(py_files):
        modified, new_source = process_file(path)
        if not modified:
            continue
        # Verify syntax before writing
        try:
            compile(new_source, str(path), "exec")
        except SyntaxError as e:
            print(f"SYNTAX ERROR after processing {path}: {e}", file=sys.stderr)
            errors += 1
            continue
        path.write_text(new_source, encoding="utf-8")
        print(f"  cleaned: {path.relative_to(Path.cwd())}")
        changed += 1

    print(f"\nDone: {changed} files modified, {errors} errors.")


if __name__ == "__main__":
    repo = Path(__file__).resolve().parents[1]
    main([repo / "src", repo / "scripts"])
