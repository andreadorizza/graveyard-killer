#!/usr/bin/env python3
"""Read and write the notes of an Obsidian Library, with no Obsidian running.

Every agent reads and writes an Obsidian vault through this script, so properties are
written as valid YAML whatever a caption holds, a write changes only the properties it
names, and text from a post cannot turn into Obsidian tags, links or formatting.

    vault.py check <path>                         where the vault is, and whether <path> exists
    vault.py list <folder> [options]              the notes of a folder, one per line
    vault.py read <note>                          one note's properties and body
    vault.py search <folder> <word>...            the notes that hold every word, one per line
    vault.py shares <note> [<already read>]       the shares the phone appended to a note, with
                                                  those of the note's sync conflict copies
    vault.py create <folder> <name> --input <json>
    vault.py create-many <folder> --input <json>  {"notes": [{"name": ..., <as create>}, ...]}
    vault.py update <note> --input <json>
    vault.py update-many --input <json>           {"notes": [{"path": ..., <as update>}, ...]}
    vault.py move-text <from> <to> --input <json> move {"text": ...}, whole lines, to the end of <to>
    vault.py adopt <from> <to> <folder> <name> --input <json>
                                                  create a note, as create does, from the share
                                                  {"share": ..., <as create>}, and move the share
                                                  from <from> to <to>: one command, so never half done
    vault.py attach <file> <folder> <name>        copy a file into the vault, and give its link
    vault.py trash <note>                         move a note to the vault's .trash folder
    vault.py new-file <path> [--input <json>]     a new file holding {"text": ...}, or empty
    vault.py new-folder <path>                    a new folder

list takes --field NAME (the properties to show, all when none), --where CONDITION
(NAME=VALUE, NAME!=VALUE, NAME~TEXT for "contains", NAME>=VALUE, NAME<=VALUE; NAME= for
empty), --extra path|uri|modified, and --out FILE. list and search print a first line
{"count": N}, then one note per line, and refuse to print more than LIMIT characters:
narrow the question, or write the lines to a file with --out.

Paths are absolute; a leading ~ is the home folder. Every other command prints one JSON
value. An error prints {"error": "..."} and exits with 1.

The JSON goes in a file, written by the agent's own file tool, never in the command:
Claude Code holds back a shell command whose text has a brace beside a quote, and text
from a post can hold anything. With no --input, the JSON is read from stdin.

The JSON for create and update:

    {"set": {"Title": "text", "tags": ["a", "b"], "Captured": {"date": "2026-11-16"},
             "Note": null},
     "unset": ["Old property"],
     "body": "<the whole new body, as Markdown>",
     "prepend": [<parts>], "append": [<parts>],
     "sections": [{"heading": "Transcript", "parts": [<parts>]}]}

A text value is written on one line: line breaks become spaces. null leaves the property
with no value. tags are made into Obsidian tags: no "#", no spaces. A part is
{"markdown": "..."} (written as it is), {"heading": "..."} (a "## " heading) or
{"post": "..."} (text from a post, escaped so that Obsidian shows it as written). A
section replaces the "## <heading>" section of that name, or is added at the end.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
import unicodedata
from datetime import date, datetime
from pathlib import Path
from typing import Any, NoReturn
from urllib.parse import quote

Properties = dict[str, Any]

# What list and search print at most: Claude Code cuts a command's output at 30,000 characters.
LIMIT = 25_000
# A key line at the top level of the frontmatter: not indented, not a list item, not a comment.
KEY_START = re.compile(r"[^\s#-]|-[^\s]")
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
NUMBER = re.compile(r"[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?")
# A key that YAML reads as written, with no quotes.
PLAIN_KEY = re.compile(r"[^\s\"'#\-?:,\[\]{}&*!|>%@`][^:#]*(?<!\s)")
# Characters YAML wants escaped inside double quotes, beyond what JSON escapes.
YAML_ESCAPE = re.compile("[\\x7f-\\x9f\\u2028\\u2029\\ufeff]")
# Characters not allowed in a note's name: by Windows, macOS, or Obsidian's links.
NAME_FORBIDDEN = re.compile(r'[\\/:*?"<>|#^\[\]\x00-\x1f]')
# A link, up to the first character that a link cannot hold as it is.
URL = re.compile(r"https?://[^\s<>\[\]\"|`{}^]+")
# Markdown that Obsidian would act on inside text from a post.
ESCAPE_CHARS = re.compile(r"([\\`*_\[\]#<>|$^])")
ESCAPE_PAIRS = re.compile(r"(==|~~|%%)")
ENTITY = re.compile(r"&(?=#?\w+;)")
UNESCAPE = re.compile(r"\\([!-/:-@\[-`{-~])")
# At a line's start, these make a list, a heading underline or a rule.
LINE_MARK = re.compile(r"^(\s*)([-+=])", re.MULTILINE)
LINE_NUMBER = re.compile(r"^(\s*\d+)([.)])(?=\s|$)", re.MULTILINE)
LINE_BREAKS = re.compile(r"\s*[\r\n]+\s*")
# What an Obsidian tag cannot hold: anything but letters, digits, "_", "-" and "/".
NOT_IN_TAG = re.compile(r"[^\w/-]+")
OPERATORS = ("!=", ">=", "<=", "~", "=")


def fail(message: str) -> NoReturn:
    print(json.dumps({"error": message}, ensure_ascii=False))
    sys.exit(1)


def path_arg(raw: str) -> Path:
    path = Path(raw).expanduser()
    if not path.is_absolute():
        fail(f"not an absolute path: {raw}")
    return path


# ---------- The vault ----------


def vault_root(path: Path) -> Path | None:
    """The nearest folder, from path up, that holds Obsidian's .obsidian folder."""
    for folder in (path, *path.parents):
        if (folder / ".obsidian").is_dir():
            return folder
    return None


def uri(note: Path) -> str | None:
    """The obsidian://open link to a note, by vault name and path from the vault's root."""
    root = vault_root(note.parent)
    if root is None:
        return None
    relative = note.relative_to(root).as_posix()
    if relative.endswith(".md"):
        relative = relative[:-3]
    return f"obsidian://open?vault={quote(root.name, safe='')}&file={quote(relative, safe='')}"


def wikilink(target: Path) -> str:
    root = vault_root(target.parent)
    relative = target.relative_to(root).as_posix() if root else target.name
    return f"[[{relative}]]"


def modified(note: Path) -> str:
    return datetime.fromtimestamp(note.stat().st_mtime).date().isoformat()


def same_name(name: str) -> str:
    """A name as macOS and Windows compare names: any Unicode form, any case."""
    return unicodedata.normalize("NFC", name).casefold()


# ---------- Frontmatter ----------


def split_note(text: str) -> tuple[list[str] | None, str]:
    """The frontmatter's lines, or None when the note has none, and the body."""
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---\n", 3)
    if end == -1:
        if text.endswith("\n---"):
            return text[4:-4].split("\n"), ""
        return None, text
    inner = text[4:end]
    return (inner.split("\n") if inner else []), text[end + 5 :]


def split_key(line: str) -> tuple[str, str] | None:
    """A top-level line's key and the rest of the line after its colon."""
    if not KEY_START.match(line):
        return None
    if line[0] in "\"'":
        quote_char = line[0]
        i = 1
        while i < len(line):
            if quote_char == '"' and line[i] == "\\":
                i += 2
                continue
            if line[i] == quote_char:
                if quote_char == "'" and line[i + 1 : i + 2] == "'":
                    i += 2
                    continue
                break
            i += 1
        key = scalar(line[: i + 1])
        rest = line[i + 1 :].lstrip()
        if not rest.startswith(":"):
            return None
        return str(key), rest[1:].strip()
    match = re.search(r":(\s|$)", line)
    if not match:
        return None
    return line[: match.start()].rstrip(), line[match.end() :].strip()


def strip_comment(value: str) -> str:
    match = re.search(r"\s#", value)
    return value[: match.start()].rstrip() if match else value


def scalar(value: str) -> Any:
    """One YAML scalar, as Obsidian or a person writes it."""
    value = value.strip()
    if not value:
        return None
    if value.startswith('"'):
        end = value.rfind('"')
        inner = value[1:end] if end > 0 else value[1:]
        try:
            return json.loads(f'"{inner}"')
        except json.JSONDecodeError:
            return inner.replace('\\"', '"').replace("\\\\", "\\")
    if value.startswith("'"):
        end = value.rfind("'")
        return (value[1:end] if end > 0 else value[1:]).replace("''", "'")
    value = strip_comment(value)
    if value in ("~", "null", "Null", "NULL"):
        return None
    if value in ("true", "True", "TRUE"):
        return True
    if value in ("false", "False", "FALSE"):
        return False
    if NUMBER.fullmatch(value):
        return float(value) if any(c in value for c in ".eE") else int(value)
    return value


def flow_list(value: str) -> list[Any]:
    inner = value.strip()[1:-1]
    items, current, in_quote = [], "", ""
    for char in inner:
        if in_quote:
            current += char
            if char == in_quote:
                in_quote = ""
        elif char in "\"'":
            in_quote = char
            current += char
        elif char == ",":
            items.append(current)
            current = ""
        else:
            current += char
    if current.strip():
        items.append(current)
    return [scalar(item) for item in items if item.strip()]


def block(lines: list[str], style: str) -> str:
    indent = min((len(line) - len(line.lstrip()) for line in lines if line.strip()), default=0)
    texts = [line[indent:] for line in lines]
    while texts and not texts[-1].strip():
        texts.pop()
    if style.startswith(">"):
        return " ".join(t.strip() for t in texts if t.strip())
    return "\n".join(texts)


def parse_frontmatter(lines: list[str]) -> tuple[Properties, dict[str, tuple[int, int]]]:
    """The properties, and the lines each top-level key spans, from its key line to the next key."""
    starts: list[tuple[int, str, str]] = []
    for i, line in enumerate(lines):
        found = split_key(line) if line and not line[0].isspace() else None
        if found:
            starts.append((i, *found))
    properties: Properties = {}
    spans: dict[str, tuple[int, int]] = {}
    for n, (start, key, rest) in enumerate(starts):
        end = starts[n + 1][0] if n + 1 < len(starts) else len(lines)
        spans[key] = (start, end)
        following = lines[start + 1 : end]
        content = [line for line in following if line.strip() and not line.lstrip().startswith("#")]
        items = [line.strip()[1:].strip() for line in content if line.strip().startswith("-")]
        if rest.startswith("["):
            properties[key] = flow_list(rest)
        elif rest[:1] in ("|", ">"):
            properties[key] = block(following, rest)
        elif not rest and items:
            properties[key] = [scalar(item) for item in items]
        elif not rest and content:
            properties[key] = "\n".join(line.strip() for line in content)
        else:
            properties[key] = scalar(rest)
    return properties, spans


def yaml_string(text: str) -> str:
    dumped = json.dumps(text, ensure_ascii=False)
    return YAML_ESCAPE.sub(lambda m: f"\\u{ord(m.group()):04x}", dumped)


def yaml_key(key: str) -> str:
    return key if PLAIN_KEY.fullmatch(key) and ": " not in key else yaml_string(key)


def one_line(text: str) -> str:
    """The text on one line: each line break, with the spaces around it, becomes one space."""
    return LINE_BREAKS.sub(" ", text).strip()


def tags(value: Any) -> list[str] | None:
    """Obsidian tags: a list, each with no "#", spaces or marks a tag cannot hold, and not only digits."""
    if value is None:
        return None
    items = value if isinstance(value, list) else [value]
    clean: list[str] = []
    for item in items:
        tag = NOT_IN_TAG.sub("-", str(item).strip().lstrip("#")).strip("-/")
        tag = re.sub(r"-{2,}", "-", tag)
        if tag and not tag.isdigit() and same_name(tag) not in map(same_name, clean):
            clean.append(tag)
    return clean


def property_lines(key: str, value: Any) -> list[str]:
    name = yaml_key(key)
    if value is None:
        return [f"{name}:"]
    if isinstance(value, bool):
        return [f"{name}: {'true' if value else 'false'}"]
    if isinstance(value, (int, float)):
        return [f"{name}: {value}"]
    if isinstance(value, dict):
        if set(value) != {"date"} or not DATE.fullmatch(str(value["date"])):
            fail(f'{key}: a date is {{"date": "YYYY-MM-DD"}}')
        try:
            date.fromisoformat(str(value["date"]))
        except ValueError:
            fail(f"{key}: {value['date']} is not a date")
        return [f"{name}: {value['date']}"]
    if isinstance(value, list):
        if not value:
            return [f"{name}: []"]
        return [f"{name}:", *(f"  - {yaml_string(one_line(str(item)))}" for item in value)]
    return [f"{name}: {yaml_string(one_line(str(value)))}"]


def set_properties(lines: list[str], changes: Properties, unset: list[str]) -> list[str]:
    """The frontmatter with these properties set or removed, every other line kept as it was."""
    changes = {k: (tags(v) if k == "tags" else v) for k, v in changes.items()}
    for key in [*changes, *unset]:
        _, spans = parse_frontmatter(lines)
        if key not in spans:
            continue
        start, end = spans[key]
        # Keep the comment and blank lines that end the span: they belong to what follows.
        while end > start + 1 and (not lines[end - 1].strip() or lines[end - 1].lstrip().startswith("#")):
            end -= 1
        replacement = property_lines(key, changes[key]) if key in changes else []
        lines = [*lines[:start], *replacement, *lines[end:]]
    _, spans = parse_frontmatter(lines)
    for key, value in changes.items():
        if key not in spans:
            lines = [*lines, *property_lines(key, value)]
    return lines


# ---------- Text from a post ----------


def escape(text: str) -> str:
    """Text from a post, so that Obsidian shows it as written: no tags, links, formatting or lists.

    Links are left whole, so that they still open.
    """
    pieces: list[str] = []
    last = 0
    for match in URL.finditer(text):
        pieces.append(escape_plain(text[last : match.start()]))
        pieces.append(match.group())
        last = match.end()
    pieces.append(escape_plain(text[last:]))
    text = LINE_MARK.sub(lambda m: f"{m.group(1)}\\{m.group(2)}", "".join(pieces))
    return LINE_NUMBER.sub(lambda m: f"{m.group(1)}\\{m.group(2)}", text)


def escape_plain(text: str) -> str:
    text = ENTITY.sub(r"\\&", ESCAPE_CHARS.sub(r"\\\1", text))
    return ESCAPE_PAIRS.sub(lambda m: "".join(f"\\{c}" for c in m.group()), text)


def render(parts: Any) -> str:
    if not isinstance(parts, list):
        fail('parts are a list of {"markdown"}, {"heading"} or {"post"} parts')
    out: list[str] = []
    for part in parts:
        if not isinstance(part, dict) or len(part) != 1:
            fail('each part is one of {"markdown": ...}, {"heading": ...}, {"post": ...}')
        kind, value = next(iter(part.items()))
        if kind == "markdown":
            out.append(str(value).strip("\n"))
        elif kind == "heading":
            out.append(f"## {one_line(str(value))}")
        elif kind == "post":
            out.append(escape(str(value).strip("\n")))
        else:
            fail(f"unknown part {kind}")
    return "\n\n".join(p for p in out if p)


def put_section(body: str, heading: str, text: str) -> str:
    """The body with its "## heading" section holding text: replaced where it is, or added at the end."""
    title = f"## {one_line(heading)}"
    section = f"{title}\n\n{text}" if text else title
    lines = body.split("\n")
    if title in lines:
        start = lines.index(title)
        end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
        rest = "\n".join(lines[end:]).strip("\n")
        before = "\n".join(lines[:start]).rstrip("\n")
        joined = "\n\n".join(p for p in (before, section, rest) if p)
        return joined + "\n"
    return f"{body.rstrip(chr(10))}\n\n{section}\n" if body.strip() else f"{section}\n"


# ---------- Reading and writing notes ----------


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    except FileNotFoundError:
        fail(f"no such file: {path}")
    except UnicodeDecodeError:
        fail(f"not a text file: {path}")


def write_text(path: Path, text: str) -> None:
    """Replace a file through a temporary file, so that a reader never sees half a note."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=".gk-", suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as out:
            out.write(text)
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def write_new(path: Path, text: str) -> None:
    """Make a new file, and fail rather than replace one that exists."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(path, "x", encoding="utf-8", newline="\n") as out:
            out.write(text)
    except FileExistsError:
        fail(f"already exists: {path}")


def load(note: Path) -> tuple[list[str] | None, str]:
    return split_note(read_text(note))


def dump(frontmatter: list[str] | None, body: str) -> str:
    if frontmatter is None:
        return body
    inner = "\n".join(frontmatter)
    return f"---\n{inner}\n---\n{body}" if inner else f"---\n---\n{body}"


def properties_of(frontmatter: list[str] | None) -> Properties:
    return parse_frontmatter(frontmatter)[0] if frontmatter is not None else {}


def apply(frontmatter: list[str] | None, body: str, change: dict[str, Any]) -> tuple[list[str], str]:
    unknown = set(change) - {"set", "unset", "body", "prepend", "append", "sections"}
    if unknown:
        fail(f"unknown keys: {', '.join(sorted(unknown))}")
    sets = change.get("set") or {}
    unset = change.get("unset") or []
    sections = change.get("sections") or []
    if not isinstance(sets, dict) or not isinstance(unset, list) or not isinstance(sections, list):
        fail("set is an object, and unset and sections are lists")
    lines = set_properties(frontmatter or [], sets, [str(k) for k in unset])
    if "body" in change:
        body = str(change["body"]).strip("\n") + "\n"
    if "prepend" in change:
        text = render(change["prepend"])
        body = f"{text}\n\n{body.lstrip(chr(10))}" if body.strip() else f"{text}\n"
    if "append" in change:
        text = render(change["append"])
        body = f"{body.rstrip(chr(10))}\n\n{text}\n" if body.strip() else f"{text}\n"
    for section in sections:
        if not isinstance(section, dict) or set(section) != {"heading", "parts"}:
            fail('each section is {"heading": ..., "parts": [...]}')
        body = put_section(body, str(section["heading"]), render(section["parts"]))
    return lines, body


INPUT: str | None = None


def input_json() -> dict[str, Any]:
    """The command's JSON: from the --input file, else from stdin."""
    if INPUT is not None:
        try:
            text = path_arg(INPUT).read_text(encoding="utf-8-sig")
        except OSError as error:
            fail(f"cannot read --input: {error}")
    else:
        text = "" if sys.stdin is None or sys.stdin.isatty() else sys.stdin.read()
    try:
        data = json.loads(text or "{}")
    except json.JSONDecodeError as error:
        fail(f"the input is not JSON: {error}")
    if not isinstance(data, dict):
        fail("the input is a JSON object")
    return data


def free_name(folder: Path, name: str, suffix: str) -> Path:
    """A file name in folder from name, safe on every system and not taken, in any case or Unicode form."""
    clean = " ".join(NAME_FORBIDDEN.sub(" ", unicodedata.normalize("NFC", name)).split()).strip(". ") or "Untitled"
    if len(clean) > 80:
        clean = clean[:80].rsplit(" ", 1)[0].rstrip(". ") or clean[:80]
    taken = {same_name(p.name) for p in folder.iterdir()} if folder.is_dir() else set()
    candidate, n = f"{clean}{suffix}", 1
    while same_name(candidate) in taken:
        n += 1
        candidate = f"{clean} {n}{suffix}"
    return folder / candidate


def notes(folder: Path) -> list[Path]:
    if not folder.is_dir():
        fail(f"no such folder: {folder}")
    return sorted(p for p in folder.iterdir() if p.suffix == ".md" and p.is_file() and not p.name.startswith("."))


# ---------- Lists ----------


def condition(text: str) -> tuple[str, str, str]:
    for i in range(len(text)):
        for op in OPERATORS:
            if text.startswith(op, i) and i > 0:
                return text[:i], op, text[i + len(op) :]
    fail(f"not a condition: {text}")


def holds(properties: Properties, where: tuple[str, str, str]) -> bool:
    name, op, wanted = where
    value = properties.get(name)
    values = [str(v) for v in (value if isinstance(value, list) else [value]) if v is not None and v != ""]
    if op == "=":
        return not values if wanted == "" else wanted in values
    if op == "!=":
        return bool(values) if wanted == "" else wanted not in values
    if op == "~":
        return any(wanted.casefold() in v.casefold() for v in values)
    if op == ">=":
        return any(v >= wanted for v in values)
    return any(v <= wanted for v in values)


def print_lines(items: list[dict[str, Any]], out: str | None) -> None:
    lines = [json.dumps(item, ensure_ascii=False) for item in items]
    if out:
        target = path_arg(out)
        write_text(target, "".join(f"{line}\n" for line in lines))
        print(json.dumps({"count": len(lines), "out": str(target)}))
        return
    text = "\n".join([json.dumps({"count": len(lines)}), *lines])
    if len(text) > LIMIT:
        fail(f"{len(lines)} notes make {len(text)} characters, more than one answer holds: "
             "ask for fewer fields, add a --where, or write them to a file with --out and read it in parts")
    print(text)


# ---------- Commands ----------


def cmd_check(args: argparse.Namespace) -> Any:
    path = path_arg(args.path).resolve()
    root = vault_root(path if path.is_dir() else path.parent)
    return {"path": str(path), "exists": path.exists(), "vault": str(root) if root else None,
            "vault_name": root.name if root else None}


def cmd_list(args: argparse.Namespace) -> None:
    wheres = [condition(w) for w in args.where or []]
    items = []
    for note in notes(path_arg(args.folder)):
        properties = properties_of(load(note)[0])
        if not all(holds(properties, w) for w in wheres):
            continue
        shown = properties if args.field is None else {k: v for k, v in properties.items() if k in args.field}
        item: dict[str, Any] = {"name": note.stem, "properties": shown}
        for extra in args.extra or []:
            item[extra] = {"path": str(note), "uri": uri(note), "modified": modified(note)}[extra]
        items.append(item)
    print_lines(items, args.out)


def cmd_read(args: argparse.Namespace) -> Any:
    note = path_arg(args.note)
    frontmatter, body = load(note)
    return {"path": str(note), "name": note.stem, "uri": uri(note), "modified": modified(note),
            "properties": properties_of(frontmatter), "body": body}


def cmd_search(args: argparse.Namespace) -> None:
    words = [w.casefold() for w in args.words]
    items = []
    for note in notes(path_arg(args.folder)):
        frontmatter, body = load(note)
        properties = properties_of(frontmatter)
        values = " ".join(json.dumps(v, ensure_ascii=False) for v in properties.values()).casefold()
        plain = UNESCAPE.sub(r"\1", body).casefold()
        if all(w in values or w in plain for w in words):
            items.append({"name": note.stem, "uri": uri(note), "properties": properties,
                          "in_body": [w for w in words if w not in values]})
    print_lines(items, None)


def split_shares(body: str) -> list[str]:
    """The shares in a body: each one ends at a line that holds a link.

    Obsidian on Android adds each share on a new line: a link alone, or a caption of several
    paragraphs and then the link, as Instagram shares a reel (tested on a Pixel, 2026-11-16).
    So the lines before a share's link line, back to the share before, are its caption, and
    text after the last link is a share with no link. A caption line that holds a link of its
    own splits the caption in two, but no share is ever lost. A share is whole lines of the
    body, without the blank lines around it, so that move-text finds it as it is.
    """
    shares: list[str] = []
    lines: list[str] = []
    for line in body.split("\n"):
        if not lines and not line.strip():
            continue
        lines.append(line)
        if URL.search(line):
            shares.append("\n".join(lines))
            lines = []
    while lines and not lines[-1].strip():
        lines.pop()
    if lines:
        shares.append("\n".join(lines))
    return shares


def share_link(text: str) -> str | None:
    """A share's link: the last one on its last line, else the first in its text, else None."""
    on_last = URL.findall(text.split("\n")[-1])
    if on_last:
        return str(on_last[-1])
    first = URL.search(text)
    return first.group() if first else None


def conflict_copies(note: Path) -> list[Path]:
    """The copies of a note that a sync app made when the note changed on two devices at once.

    Syncthing names one "<name>.sync-conflict-<date>-<time>-<device>.md", and Obsidian Sync,
    set to create conflict files, "<name> (Conflicted copy <device> <time>).md".
    """
    stem = re.escape(unicodedata.normalize("NFC", note.stem))
    pattern = re.compile(rf"{stem}(\.sync-conflict-.+| \(Conflicted copy .+\))\.md")
    return sorted(p for p in note.parent.iterdir()
                  if p.is_file() and pattern.fullmatch(unicodedata.normalize("NFC", p.name)))


def cmd_shares(args: argparse.Namespace) -> Any:
    """The shares in a note, after folding in the shares of its conflict copies.

    A conflict copy holds the version of the note that lost: from the phone, a share added
    while this computer moved others out; or from this computer, without the shares the
    phone kept. So its shares not yet in the note or in the Already read note are added to
    the note, the shares already in Already read leave the note, and the copy goes to the
    vault's .trash folder. Written first, trashed after: stopped halfway, the next call
    finds the same shares and adds none twice.
    """
    note = path_arg(args.note)
    copies = conflict_copies(note)
    frontmatter, body = load(note)
    changed = max(p.stat().st_mtime for p in [note, *copies])
    shares = split_shares(body)
    if copies:
        done = load(path_arg(args.already_read))[1] if args.already_read else ""
        kept: list[str] = []
        for text in shares + [t for copy in copies for t in split_shares(load(copy)[1])]:
            if text not in kept and whole_lines(done, escape(text)) == -1:
                kept.append(text)
        if kept != shares:
            write_text(note, dump(frontmatter, "\n\n".join(kept) + "\n" if kept else ""))
            shares = kept
        root = vault_root(note.parent)
        for copy in copies:
            if root is not None:
                trashed = free_name(root / ".trash", copy.stem, copy.suffix)
                trashed.parent.mkdir(exist_ok=True)
                os.replace(copy, trashed)
    found = [{"text": text, "link": share_link(text)} for text in shares]
    return {"modified": datetime.fromtimestamp(changed).date().isoformat(), "shares": found,
            "merged": [copy.name for copy in copies]}


def cmd_create(args: argparse.Namespace) -> Any:
    change = input_json()
    note = free_name(path_arg(args.folder), args.name, ".md")
    lines, body = apply([], "", change)
    write_new(note, dump(lines or None, body))
    return {"path": str(note), "uri": uri(note), "name": note.stem}


def cmd_update(args: argparse.Namespace) -> Any:
    note = path_arg(args.note)
    change = input_json()
    frontmatter, body = load(note)
    lines, body = apply(frontmatter, body, change)
    write_text(note, dump(lines if (lines or frontmatter is not None) else None, body))
    return {"path": str(note), "uri": uri(note), "name": note.stem}


def batch(key: str) -> list[dict[str, Any]]:
    """The notes of a many command, each with its key, checked before anything is written."""
    items = input_json().get("notes")
    if not isinstance(items, list) or not all(isinstance(i, dict) and isinstance(i.get(key), str) for i in items):
        fail(f'the input is {{"notes": [{{"{key}": ..., ...}}, ...]}}')
    return items


def cmd_create_many(args: argparse.Namespace) -> Any:
    folder = path_arg(args.folder)
    ready = [(item["name"], apply([], "", {k: v for k, v in item.items() if k != "name"})) for item in batch("name")]
    made = []
    for name, (lines, body) in ready:
        note = free_name(folder, name, ".md")
        write_new(note, dump(lines or None, body))
        made.append({"path": str(note), "uri": uri(note), "name": note.stem})
    return made


def cmd_update_many(args: argparse.Namespace) -> Any:
    ready = []
    for item in batch("path"):
        note = path_arg(item["path"])
        frontmatter, body = load(note)
        lines, body = apply(frontmatter, body, {k: v for k, v in item.items() if k != "path"})
        ready.append((note, dump(lines if (lines or frontmatter is not None) else None, body)))
    for note, text in ready:
        write_text(note, text)
    return [{"path": str(note), "uri": uri(note), "name": note.stem} for note, _ in ready]


def whole_lines(body: str, text: str) -> int:
    """Where text sits in body as whole lines, or -1."""
    at = body.find(text)
    while at != -1:
        end = at + len(text)
        if (at == 0 or body[at - 1] == "\n") and (end == len(body) or body[end] == "\n"):
            return at
        at = body.find(text, at + 1)
    return -1


def cmd_move_text(args: argparse.Namespace) -> Any:
    move_text(path_arg(args.source), path_arg(args.target), input_json().get("text", ""))
    return {"moved": True, "from": args.source, "to": args.target}


def cmd_adopt(args: argparse.Namespace) -> Any:
    source, target = path_arg(args.source), path_arg(args.target)
    change = input_json()
    share = change.pop("share", "")
    find_lines(source, share)  # before anything is written
    note = free_name(path_arg(args.folder), args.name, ".md")
    lines, body = apply([], "", change)
    write_new(note, dump(lines or None, body))
    move_text(source, target, share)
    return {"path": str(note), "uri": uri(note), "name": note.stem, "moved": True}


def find_lines(source: Path, raw: Any) -> tuple[list[str] | None, str, str, int]:
    text = str(raw).replace("\r\n", "\n").strip("\n")
    if not text.strip():
        fail("no text to move")
    frontmatter, body = load(source)
    at = whole_lines(body, text)
    if at == -1:
        fail("the text is not in the note as whole lines: run shares again")
    return frontmatter, body, text, at


def move_text(source: Path, target: Path, raw: Any) -> None:
    frontmatter, body, text, at = find_lines(source, raw)
    # Add to the target first: if anything stops halfway, the text is in both notes, never in neither.
    # It goes there escaped, so that a caption's hashtags make no tags in the vault.
    target_front, target_body = load(target) if target.exists() else (None, "")
    kept = escape(text)
    target_body = f"{target_body.rstrip(chr(10))}\n\n{kept}\n" if target_body.strip() else f"{kept}\n"
    write_text(target, dump(target_front, target_body))
    before, after = body[:at].rstrip("\n"), body[at + len(text) :].lstrip("\n")
    rest = f"{before}\n\n{after}" if before and after else before or after
    write_text(source, dump(frontmatter, rest.rstrip("\n") + "\n" if rest.strip() else ""))


def cmd_attach(args: argparse.Namespace) -> Any:
    source = path_arg(args.file)
    if not source.is_file():
        fail(f"no such file: {source}")
    folder = path_arg(args.folder)
    folder.mkdir(parents=True, exist_ok=True)
    target = free_name(folder, args.name, source.suffix.lower())
    try:
        with open(source, "rb") as reader, open(target, "xb") as writer:
            shutil.copyfileobj(reader, writer)
    except FileExistsError:
        fail(f"already exists: {target}")
    return {"path": str(target), "link": wikilink(target)}


def cmd_trash(args: argparse.Namespace) -> Any:
    note = path_arg(args.note).resolve()
    if not note.is_file():
        fail(f"no such file: {note}")
    root = vault_root(note.parent)
    if root is None:
        fail("the note is not in an Obsidian vault")
    target = free_name(root / ".trash", note.stem, note.suffix)
    target.parent.mkdir(exist_ok=True)
    os.replace(note, target)
    return {"trashed": str(note), "path": str(target)}


def cmd_new_file(args: argparse.Namespace) -> Any:
    path = path_arg(args.path)
    write_new(path, str(input_json().get("text", "")))
    return {"path": str(path), "uri": uri(path) if path.suffix == ".md" else None}


def cmd_new_folder(args: argparse.Namespace) -> Any:
    path = path_arg(args.path)
    path.mkdir(parents=True, exist_ok=True)
    return {"path": str(path)}


def main() -> None:
    global INPUT
    parser = argparse.ArgumentParser(prog="vault.py", description=__doc__.replace("LIMIT", f"{LIMIT:,}"),
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check").add_argument("path")
    listing = commands.add_parser("list")
    listing.add_argument("folder")
    listing.add_argument("--field", action="append")
    listing.add_argument("--where", action="append")
    listing.add_argument("--extra", action="append", choices=("path", "uri", "modified"))
    listing.add_argument("--out")
    commands.add_parser("read").add_argument("note")
    search = commands.add_parser("search")
    search.add_argument("folder")
    search.add_argument("words", nargs="+")
    shares = commands.add_parser("shares")
    shares.add_argument("note")
    shares.add_argument("already_read", nargs="?")
    create = commands.add_parser("create")
    create.add_argument("folder")
    create.add_argument("name")
    commands.add_parser("create-many").add_argument("folder")
    commands.add_parser("update").add_argument("note")
    commands.add_parser("update-many")
    move = commands.add_parser("move-text")
    move.add_argument("source")
    move.add_argument("target")
    adopt = commands.add_parser("adopt")
    for name in ("source", "target", "folder", "name"):
        adopt.add_argument(name)
    attach = commands.add_parser("attach")
    attach.add_argument("file")
    attach.add_argument("folder")
    attach.add_argument("name")
    commands.add_parser("trash").add_argument("note")
    commands.add_parser("new-file").add_argument("path")
    commands.add_parser("new-folder").add_argument("path")
    for name in ("create", "create-many", "update", "update-many", "move-text", "adopt", "new-file"):
        commands.choices[name].add_argument("--input", metavar="JSON_FILE")
    args = parser.parse_args()
    INPUT = getattr(args, "input", None)

    handlers = {"check": cmd_check, "list": cmd_list, "read": cmd_read, "search": cmd_search,
                "shares": cmd_shares, "create": cmd_create, "create-many": cmd_create_many,
                "update": cmd_update, "update-many": cmd_update_many, "move-text": cmd_move_text, "adopt": cmd_adopt,
                "attach": cmd_attach, "trash": cmd_trash, "new-file": cmd_new_file,
                "new-folder": cmd_new_folder}
    try:
        result = handlers[args.command](args)
    except OSError as error:
        fail(f"{type(error).__name__}: {error}")
    if result is not None:
        print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")
    main()
