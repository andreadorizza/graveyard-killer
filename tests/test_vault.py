"""The vault script, called the way the agent calls it: arguments and JSON in, JSON out."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
import yaml

SCRIPT = Path(__file__).parent.parent / "plugin/skills/graveyard-killer/scripts/vault.py"


def run(*args: str | Path, stdin: dict[str, Any] | None = None, ok: bool = True) -> str:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, args)],
        input=json.dumps(stdin) if stdin is not None else "",
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert (result.returncode == 0) == ok, result.stdout + result.stderr
    return result.stdout


def vault(*args: str | Path, stdin: dict[str, Any] | None = None, ok: bool = True) -> Any:
    return json.loads(run(*args, stdin=stdin, ok=ok))


def notes_listed(*args: str | Path) -> list[dict[str, Any]]:
    """What list or search prints: a count, then one note per line."""
    first, *rest = run(*args).splitlines()
    assert json.loads(first) == {"count": len(rest)}
    return [json.loads(line) for line in rest]


@pytest.fixture
def library(tmp_path: Path) -> Path:
    """A Library folder inside an Obsidian vault named "My Vault"."""
    root = tmp_path / "My Vault"
    (root / ".obsidian").mkdir(parents=True)
    folder = root / "Graveyard Killer"
    (folder / "Entries").mkdir(parents=True)
    return folder


def frontmatter(note: Path) -> Any:
    """The note's frontmatter as a real YAML parser reads it."""
    text = note.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    return yaml.safe_load(text[4 : text.index("\n---\n", 3)])


HOSTILE = [
    'She said "hi": it\'s #great',
    "- starts like a list",
    "=1+1",
    "007",
    "yes",
    "null",
    "2026-11-16",
    "@handle & co: 50% off!",
    "emoji 🍝 and a\u2028line separator",
    "back\\slash and a tab\there",
    "[[Not a link]] {not: a map}",
]


@pytest.mark.parametrize("text", HOSTILE)
def test_any_text_is_written_as_text_and_read_back_as_written(library: Path, text: str) -> None:
    made = vault("create", library / "Entries", "Post", stdin={"set": {"Caption": text}})
    note = Path(made["path"])

    assert vault("read", note)["properties"]["Caption"] == text
    assert frontmatter(note)["Caption"] == text


def test_the_json_can_come_from_a_file(library: Path, tmp_path: Path) -> None:
    payload = tmp_path / "input.json"
    payload.write_text(json.dumps({"set": {"Caption": '{"braces": "and quotes"} $(not run) `nor this`'}}), encoding="utf-8")

    made = vault("create", library / "Entries", "Post", "--input", payload)

    assert vault("read", made["path"])["properties"]["Caption"] == '{"braces": "and quotes"} $(not run) `nor this`'


def test_a_text_value_is_written_on_one_line(library: Path) -> None:
    made = vault("create", library / "Entries", "Post", stdin={"set": {"Summary": "First line\n\n  second line  "}})

    assert vault("read", made["path"])["properties"]["Summary"] == "First line second line"


def test_dates_lists_and_empty_values_have_obsidian_types(library: Path) -> None:
    made = vault("create", library / "Entries", "Post", stdin={"set": {
        "Captured": {"date": "2026-11-16"},
        "tags": ["cucina", "pasta-veloce"],
        "Note": None,
        "Prossima azione": "Cucinarla sabato",
    }})
    note = Path(made["path"])
    text = note.read_text(encoding="utf-8")

    assert "Captured: 2026-11-16\n" in text  # unquoted, so Obsidian reads a date
    assert "tags:\n  - \"cucina\"\n  - \"pasta-veloce\"\n" in text
    assert "Note:\n" in text
    data = frontmatter(note)
    assert str(data["Captured"]) == "2026-11-16"
    assert data["tags"] == ["cucina", "pasta-veloce"]
    assert data["Note"] is None
    assert data["Prossima azione"] == "Cucinarla sabato"
    assert vault("read", note)["properties"]["Captured"] == "2026-11-16"


def test_a_bad_date_is_refused(library: Path) -> None:
    out = vault("create", library / "Entries", "Post", stdin={"set": {"Captured": {"date": "2026-13-45"}}}, ok=False)

    assert "not a date" in out["error"]
    assert list((library / "Entries").iterdir()) == []


OBSIDIAN_WRITTEN = """---
Titolo: Pasta alla Norma
Link: https://www.instagram.com/p/DQx1abc/
"Strana: chiave": valore
'Citata': 'l''altra'
tags:
  - cucina
  - "pasta veloce"
Elenco: [uno, "due, tre"]
Fatto: true
Porzioni: 4
Catturato il: 2026-11-10
Vuota:
# a comment the user wrote
Mappa:
  dentro: 1
Blocco: |
  riga uno
  riga due
Nota: ciao # commento
---
Body text.
"""


def test_reads_what_obsidian_and_people_write(library: Path) -> None:
    note = library / "Entries" / "Norma.md"
    note.write_text(OBSIDIAN_WRITTEN, encoding="utf-8")

    properties = vault("read", note)["properties"]

    assert properties["Titolo"] == "Pasta alla Norma"
    assert properties["Link"] == "https://www.instagram.com/p/DQx1abc/"
    assert properties["Strana: chiave"] == "valore"
    assert properties["Citata"] == "l'altra"
    assert properties["tags"] == ["cucina", "pasta veloce"]
    assert properties["Elenco"] == ["uno", "due, tre"]
    assert properties["Fatto"] is True
    assert properties["Porzioni"] == 4
    assert properties["Catturato il"] == "2026-11-10"
    assert properties["Vuota"] is None
    assert properties["Mappa"] == "dentro: 1"
    assert properties["Blocco"] == "riga uno\nriga due"
    assert properties["Nota"] == "ciao"
    assert vault("read", note)["body"] == "Body text.\n"


def test_an_update_changes_only_the_properties_it_names(library: Path) -> None:
    note = library / "Entries" / "Norma.md"
    note.write_text(OBSIDIAN_WRITTEN, encoding="utf-8")

    vault("update", note, stdin={"set": {"tags": ["cucina", "sicilia"], "Nota": None, "Stato": "Elaborato"},
                                 "unset": ["Porzioni"]})

    after = note.read_text(encoding="utf-8")
    expected = (
        OBSIDIAN_WRITTEN.replace('  - "pasta veloce"\n', "")
        .replace("tags:\n  - cucina\n", 'tags:\n  - "cucina"\n  - "sicilia"\n')
        .replace("Porzioni: 4\n", "")
        .replace("Nota: ciao # commento\n", 'Nota:\nStato: "Elaborato"\n')
    )
    assert after == expected
    assert frontmatter(note)["Stato"] == "Elaborato"


def test_an_update_keeps_a_comment_after_the_property_it_changes(library: Path) -> None:
    note = library / "Entries" / "Norma.md"
    note.write_text(OBSIDIAN_WRITTEN, encoding="utf-8")

    vault("update", note, stdin={"set": {"Vuota": "piena"}})

    assert 'Vuota: "piena"\n# a comment the user wrote\nMappa:' in note.read_text(encoding="utf-8")


def test_a_note_with_no_frontmatter_gets_one_on_its_first_property(library: Path) -> None:
    note = library / "Share here.md"
    note.write_text("just text\n", encoding="utf-8")

    vault("update", note, stdin={"append": [{"markdown": "more"}]})
    assert note.read_text(encoding="utf-8") == "just text\n\nmore\n"

    vault("update", note, stdin={"set": {"Seen": True}})
    assert note.read_text(encoding="utf-8") == "---\nSeen: true\n---\njust text\n\nmore\n"


def test_appended_parts_go_after_the_body_and_post_text_stays_as_written(library: Path) -> None:
    made = vault("create", library / "Entries", "Post", stdin={"set": {"Titolo": "x"}, "body": "Captured again on 2026-11-12"})
    caption = "Best #pasta ever! **wow** [[link]] ==hi== %%no%% $5 &amp; ^ref\n- one\n2. two\nhttps://example.com/a_b?c=*d*"

    vault("update", made["path"], stdin={"append": [{"heading": "Didascalia"}, {"post": caption}],
                                         "prepend": [{"markdown": "Shared as: link"}]})

    body = vault("read", made["path"])["body"]
    assert body == (
        "Shared as: link\n\nCaptured again on 2026-11-12\n\n## Didascalia\n\n"
        "Best \\#pasta ever! \\*\\*wow\\*\\* \\[\\[link\\]\\] \\=\\=hi\\=\\= \\%\\%no\\%\\% \\$5 \\&amp; \\^ref\n"
        "\\- one\n2\\. two\nhttps://example.com/a_b?c=*d*\n"
    )


def test_body_replaces_the_whole_body(library: Path) -> None:
    made = vault("create", library, "Settings", stdin={"body": "## Language\nItaliano"})

    vault("update", made["path"], stdin={"body": "## Language\nEnglish\n"})

    assert Path(made["path"]).read_text(encoding="utf-8") == "## Language\nEnglish\n"


def test_names_are_safe_and_never_taken(library: Path) -> None:
    folder = library / "Entries"
    first = vault("create", folder, 'Post: "Instagram" #1 / [x]?', stdin={})
    (folder / "post.md").write_text("", encoding="utf-8")
    second = vault("create", folder, "Post", stdin={})
    third = vault("create", folder, "Post", stdin={})

    assert first["name"] == "Post Instagram 1 x"
    assert second["name"] == "Post 2"  # "post.md" takes "Post" on a system that ignores case
    assert third["name"] == "Post 3"


def test_links_open_the_note_in_its_vault(library: Path) -> None:
    made = vault("create", library / "Entries", "Pasta alla Norma", stdin={})

    assert made["uri"] == "obsidian://open?vault=My%20Vault&file=Graveyard%20Killer%2FEntries%2FPasta%20alla%20Norma"


def test_list_gives_each_note_with_the_fields_asked_for(library: Path) -> None:
    folder = library / "Entries"
    vault("create", folder, "A", stdin={"set": {"Link": "https://a", "Stato": "Da leggere", "Titolo": "A"}})
    vault("create", folder, "B", stdin={"set": {"Link": "https://b", "Stato": "Elaborato"}})
    (folder / ".hidden.md").write_text("", encoding="utf-8")
    (folder / "image.jpg").write_bytes(b"x")

    listed = notes_listed("list", folder, "--field", "Link", "--field", "Stato")

    assert listed == [{"name": "A", "properties": {"Link": "https://a", "Stato": "Da leggere"}},
                      {"name": "B", "properties": {"Link": "https://b", "Stato": "Elaborato"}}]


def test_list_filters_by_conditions_and_adds_what_is_asked(library: Path) -> None:
    folder = library / "Entries"
    vault("create-many", folder, stdin={"notes": [
        {"name": "A", "set": {"Link": "https://x.com/p/AbC/", "Stato": "Da leggere", "Catturato il": {"date": "2026-11-01"}}},
        {"name": "B", "set": {"Link": "https://x.com/p/Zz/?a=b", "Stato": "Elaborato", "Catturato il": {"date": "2026-11-10"}}},
        {"name": "C", "set": {"Link": "https://y.com/", "Nota": None, "tags": ["pasta"]}},
    ]})

    def names(*where: str) -> list[str]:
        args = [a for w in where for a in ("--where", w)]
        return [n["name"] for n in notes_listed("list", folder, "--field", "Link", *args)]

    assert names("Link=https://x.com/p/Zz/?a=b") == ["B"]
    assert names("Link~abc") == ["A"]
    assert names("Stato=") == ["C"]
    assert names("Stato!=Elaborato") == ["A", "C"]
    assert names("Catturato il>=2026-11-05") == ["B"]
    assert names("Catturato il<=2026-11-05", "Stato=Da leggere") == ["A"]
    assert names("tags=pasta") == ["C"]
    item = notes_listed("list", folder, "--field", "Link", "--where", "Stato=Elaborato",
                        "--extra", "path", "--extra", "uri", "--extra", "modified")[0]
    assert item["path"] == str(folder / "B.md")
    assert item["uri"].startswith("obsidian://open?vault=My%20Vault&file=")
    assert len(item["modified"]) == 10


def test_list_refuses_an_answer_too_long_to_print_and_can_write_it_to_a_file(library: Path, tmp_path: Path) -> None:
    folder = library / "Entries"
    vault("create-many", folder, stdin={"notes": [
        {"name": f"Instagram {i:03d}", "set": {"Link": f"https://www.instagram.com/p/{'x' * 200}{i}/"}} for i in range(150)
    ]})

    refused = vault("list", folder, ok=False)
    out = vault("list", folder, "--field", "Link", "--out", tmp_path / "links.jsonl")

    assert "--out" in refused["error"]
    assert out["count"] == 150
    written = (tmp_path / "links.jsonl").read_text(encoding="utf-8").splitlines()
    assert json.loads(written[0])["name"] == "Instagram 000"


def test_search_finds_every_word_in_properties_or_body(library: Path) -> None:
    folder = library / "Entries"
    vault("create", folder, "Norma", stdin={"set": {"Titolo": "Pasta alla Norma"}, "body": "Melanzane fritte"})
    vault("create", folder, "Carbonara", stdin={"set": {"Titolo": "Carbonara"}, "body": "Guanciale"})

    vault("update", library / "Entries" / "Carbonara.md", stdin={"append": [{"post": "fettuccine_fresche #roma"}]})

    found = notes_listed("search", folder, "PASTA", "melanzane")

    assert [n["name"] for n in found] == ["Norma"]
    assert found[0]["in_body"] == ["melanzane"]
    assert notes_listed("search", folder, "pasta", "guanciale") == []
    assert [n["name"] for n in notes_listed("search", folder, "fettuccine_fresche", "#roma")] == ["Carbonara"]


def test_many_notes_are_created_or_updated_in_one_call(library: Path) -> None:
    folder = library / "Entries"
    made = vault("create-many", folder, stdin={"notes": [
        {"name": "Instagram A1", "set": {"Stato": "Sepolto", "Salvato il": {"date": "2025-01-02"}}},
        {"name": "Instagram A1", "set": {"Stato": "Sepolto"}},
    ]})
    assert [m["name"] for m in made] == ["Instagram A1", "Instagram A1 2"]

    vault("update-many", stdin={"notes": [{"path": m["path"], "set": {"Stato": "Scartato"}} for m in made]})

    assert [n["properties"]["Stato"] for n in notes_listed("list", folder)] == ["Scartato", "Scartato"]


def test_a_bad_note_in_a_batch_stops_the_whole_batch(library: Path) -> None:
    folder = library / "Entries"

    vault("create-many", folder, stdin={"notes": [
        {"name": "Good", "set": {"Stato": "Sepolto"}},
        {"name": "Bad", "set": {"Salvato il": {"date": "someday"}}},
    ]}, ok=False)

    assert list(folder.iterdir()) == []


def test_move_text_moves_exact_text_to_the_end_of_another_note(library: Path) -> None:
    share = library / "Share here.md"
    share.write_text("Look https://youtu.be/a\n\nhttps://vm.tiktok.com/ZM1/ Check out this video!\n\nkeep me\n", encoding="utf-8")
    read = library / "Already read.md"

    vault("move-text", share, read, stdin={"text": "https://vm.tiktok.com/ZM1/ Check out this video!"})
    vault("move-text", share, read, stdin={"text": "Look https://youtu.be/a"})

    assert share.read_text(encoding="utf-8") == "keep me\n"
    assert read.read_text(encoding="utf-8") == "https://vm.tiktok.com/ZM1/ Check out this video!\n\nLook https://youtu.be/a\n"


def test_move_text_moves_whole_lines_only_and_escapes_what_it_keeps(library: Path) -> None:
    share = library / "Share here.md"
    share.write_text("Guarda https://youtu.be/X e altro #fyp\n\nhttps://youtu.be/X\n", encoding="utf-8")
    read = library / "Already read.md"

    vault("move-text", share, read, stdin={"text": "https://youtu.be/X"})

    assert share.read_text(encoding="utf-8") == "Guarda https://youtu.be/X e altro #fyp\n"
    vault("move-text", share, read, stdin={"text": "Guarda https://youtu.be/X e altro #fyp"})
    assert read.read_text(encoding="utf-8") == "https://youtu.be/X\n\nGuarda https://youtu.be/X e altro \\#fyp\n"


def test_move_text_refuses_text_that_is_not_there(library: Path) -> None:
    share = library / "Share here.md"
    share.write_text("https://youtu.be/a\n", encoding="utf-8")

    out = vault("move-text", share, library / "Already read.md", stdin={"text": "https://youtu.be/b"}, ok=False)

    assert "not in the note" in out["error"]
    assert share.read_text(encoding="utf-8") == "https://youtu.be/a\n"
    assert not (library / "Already read.md").exists()


def test_adopt_creates_the_entry_and_moves_the_share_in_one_command(library: Path) -> None:
    share = library / "Share here.md"
    share.write_text("Guarda https://youtu.be/a #fyp\n\nhttps://youtu.be/b\n", encoding="utf-8")
    read = library / "Already read.md"
    read.write_text("", encoding="utf-8")

    made = vault("adopt", share, read, library / "Entries", "YouTube a", stdin={
        "share": "Guarda https://youtu.be/a #fyp", "set": {"Stato": "Da leggere"},
        "prepend": [{"post": "Condiviso come: Guarda https://youtu.be/a #fyp"}]})

    assert vault("read", made["path"])["properties"] == {"Stato": "Da leggere"}
    assert share.read_text(encoding="utf-8") == "https://youtu.be/b\n"
    assert read.read_text(encoding="utf-8") == "Guarda https://youtu.be/a \\#fyp\n"


def test_adopt_writes_nothing_when_the_share_is_gone(library: Path) -> None:
    share = library / "Share here.md"
    share.write_text("https://youtu.be/b\n", encoding="utf-8")

    vault("adopt", share, library / "Already read.md", library / "Entries", "YouTube a",
          stdin={"share": "https://youtu.be/a", "set": {"Stato": "Da leggere"}}, ok=False)

    assert list((library / "Entries").iterdir()) == []
    assert not (library / "Already read.md").exists()


# What Obsidian on Android wrote, shape for shape (tested on a Pixel, 2026-11-16): an Instagram
# reel and a TikTok as bare links, one per line, then an Instagram reel shared with its caption,
# the caption first and the link last, both indented, with blank lines inside the caption.
REEL = "https://www.instagram.com/reel/A1b2C3d4E5f/?psln=QUJDREVGR0g="
TIKTOK = "https://vm.tiktok.com/ZMa1b2C3d/"
CAPTIONED = (
    "               Commenta PASTA per la ricetta 👇\n"
    "\n"
    "La pasta e patate come la faceva mia nonna.\n"
    "\n"
    "Ti serve:\n"
    "1. Pasta mista\n"
    "2. Patate e provola\n"
    "\n"
    "#pasta #ricette\n"
    "               https://www.instagram.com/reel/DgB2abc/?vrfl=SUpLTE1OT1A="
)
ANDROID = f"{REEL}\n{TIKTOK}\n\n{CAPTIONED}\n"


def test_android_shares_split_into_bare_links_and_a_captioned_reel(library: Path) -> None:
    share = library / "Share here.md"
    share.write_text(ANDROID, encoding="utf-8")

    out = vault("shares", share)

    assert [s["text"] for s in out["shares"]] == [REEL, TIKTOK, CAPTIONED]
    assert [s["link"] for s in out["shares"]] == [
        REEL, TIKTOK, "https://www.instagram.com/reel/DgB2abc/?vrfl=SUpLTE1OT1A="]
    assert len(out["modified"]) == 10


def test_adopting_the_captioned_reel_moves_its_whole_caption(library: Path) -> None:
    share = library / "Share here.md"
    share.write_text(ANDROID, encoding="utf-8")
    read = library / "Already read.md"
    captioned = vault("shares", share)["shares"][2]["text"]

    vault("adopt", share, read, library / "Entries", "Instagram DgB2abc",
          stdin={"share": captioned, "set": {"Stato": "In arrivo"}})

    assert share.read_text(encoding="utf-8") == f"{REEL}\n{TIKTOK}\n"
    moved = read.read_text(encoding="utf-8")
    assert "\\#pasta \\#ricette" in moved and "1\\. Pasta mista" in moved
    assert [s["text"] for s in vault("shares", share)["shares"]] == [REEL, TIKTOK]


def test_adopting_one_bare_link_leaves_the_next(library: Path) -> None:
    share = library / "Share here.md"
    share.write_text(f"{REEL}\n{TIKTOK}\n", encoding="utf-8")

    vault("adopt", share, library / "Already read.md", library / "Entries", "Instagram A1b2C3d4E5f",
          stdin={"share": REEL, "set": {"Stato": "In arrivo"}})

    assert share.read_text(encoding="utf-8") == f"{TIKTOK}\n"


def test_a_link_inside_a_line_ends_its_share_and_text_after_the_last_link_has_none(library: Path) -> None:
    share = library / "Share here.md"
    share.write_text("Guarda https://youtu.be/a #fyp\nhttps://youtu.be/b\n\nlatte, uova, farina\n", encoding="utf-8")

    shares = vault("shares", share)["shares"]

    assert [(s["text"], s["link"]) for s in shares] == [
        ("Guarda https://youtu.be/a #fyp", "https://youtu.be/a"),
        ("https://youtu.be/b", "https://youtu.be/b"),
        ("latte, uova, farina", None)]


FILED = "Guarda https://youtu.be/a #fyp"
NEW = "Pasta e patate #food\nhttps://www.instagram.com/reel/B2/"


def test_shares_takes_in_a_share_that_syncthing_put_in_a_conflict_copy(library: Path) -> None:
    # This computer moved FILED out; meanwhile the phone added NEW to its older copy.
    share = library / "Share here.md"
    share.write_text("", encoding="utf-8")
    read = library / "Already read.md"
    read.write_text("Guarda https://youtu.be/a \\#fyp\n", encoding="utf-8")
    copy = library / "Share here.sync-conflict-20261116-101500-ABC1234.md"
    copy.write_text(f"{FILED}\n\n{NEW}\n", encoding="utf-8")
    os.utime(share, (1_700_000_000, 1_700_000_000))
    os.utime(copy, (1_800_000_000, 1_800_000_000))

    out = vault("shares", share, read)

    assert [s["text"] for s in out["shares"]] == [NEW]
    assert out["merged"] == [copy.name]
    assert out["modified"] == datetime.fromtimestamp(1_800_000_000).date().isoformat()
    assert share.read_text(encoding="utf-8") == f"{NEW}\n"
    assert not copy.exists()
    assert (library.parent / ".trash" / copy.name).exists()


def test_shares_drops_a_filed_share_when_the_phone_won_the_conflict(library: Path) -> None:
    # The phone's version kept FILED, which this computer had moved out: this computer's is the copy.
    share = library / "Share here.md"
    share.write_text(f"{FILED}\n\n{NEW}\n", encoding="utf-8")
    read = library / "Already read.md"
    read.write_text("Guarda https://youtu.be/a \\#fyp\n", encoding="utf-8")
    (library / "Share here.sync-conflict-20261116-130000-XYZ9876.md").write_text("", encoding="utf-8")

    out = vault("shares", share, read)

    assert [s["text"] for s in out["shares"]] == [NEW]
    assert share.read_text(encoding="utf-8") == f"{NEW}\n"


def test_shares_reads_obsidian_sync_conflict_copies_and_adds_nothing_twice(library: Path) -> None:
    share = library / "Già qui.md"
    share.write_text(f"{FILED}\n", encoding="utf-8")
    nfd = unicodedata.normalize("NFD", "Già qui (Conflicted copy Pixel 9 202611161300).md")
    (library / nfd).write_text(f"{FILED}\n\n{NEW}\n", encoding="utf-8")

    first = vault("shares", share)
    again = vault("shares", share)

    assert [s["text"] for s in first["shares"]] == [FILED, NEW]
    assert len(first["merged"]) == 1
    assert again["shares"] == first["shares"] and again["merged"] == []
    assert share.read_text(encoding="utf-8") == f"{FILED}\n\n{NEW}\n"


def test_shares_with_no_conflict_copy_changes_nothing(library: Path) -> None:
    share = library / "Share here.md"
    share.write_text(f"{FILED}\n", encoding="utf-8")
    read = library / "Already read.md"
    read.write_text("Guarda https://youtu.be/a \\#fyp\n", encoding="utf-8")
    (library / "Share here 2.md").write_text(f"{NEW}\n", encoding="utf-8")

    out = vault("shares", share, read)

    assert [s["text"] for s in out["shares"]] == [FILED]
    assert out["merged"] == []
    assert (library / "Share here 2.md").exists()


def test_a_section_is_replaced_where_it_is_or_added(library: Path) -> None:
    made = vault("create", library / "Entries", "Post", stdin={
        "body": "Captured again on 2026-11-12\n\n## Didascalia\n\nold caption\n\n## Trascrizione\n\nold words"})

    vault("update", made["path"], stdin={"sections": [
        {"heading": "Didascalia", "parts": [{"post": "new #caption"}]},
        {"heading": "Testo a schermo", "parts": [{"post": "SALE 50%"}]},
    ]})

    assert vault("read", made["path"])["body"] == (
        "Captured again on 2026-11-12\n\n## Didascalia\n\nnew \\#caption\n\n## Trascrizione\n\nold words\n\n"
        "## Testo a schermo\n\nSALE 50%\n")


def test_tags_are_made_into_obsidian_tags(library: Path) -> None:
    made = vault("create", library / "Entries", "Post", stdin={"set": {"tags": [
        "#cucina", "pasta veloce", "l'arte", "c++", "2024", "Cucina", "città/roma", ""]}})

    assert vault("read", made["path"])["properties"]["tags"] == ["cucina", "pasta-veloce", "l-arte", "c", "città/roma"]


def test_a_name_in_another_unicode_form_is_taken(library: Path) -> None:
    folder = library / "Entries"
    decomposed = "Caffe\u0300"  # "Caffè" as macOS may write it
    (folder / f"{decomposed}.md").write_text("mine\n", encoding="utf-8")

    made = vault("create", folder, "Caff\u00e8", stdin={})

    assert made["name"] == "Caff\u00e8 2"
    assert (folder / f"{decomposed}.md").read_text(encoding="utf-8") == "mine\n"


def test_paths_start_from_home_and_must_be_absolute(library: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = library.parent.parent
    result = subprocess.run([sys.executable, str(SCRIPT), "check", "~/My Vault/Graveyard Killer"],
                            capture_output=True, text=True, env={**os.environ, "HOME": str(home), "USERPROFILE": str(home)})
    assert json.loads(result.stdout)["vault_name"] == "My Vault"

    out = vault("create", "Relative/Folder", "Post", stdin={}, ok=False)
    assert "absolute" in out["error"]


def test_attach_copies_a_file_and_gives_its_link_from_the_vault_root(library: Path, tmp_path: Path) -> None:
    image = tmp_path / "thumbnail.JPG"
    image.write_bytes(b"\xff\xd8 jpeg")

    first = vault("attach", image, library / "Attachments", "Instagram DQx1abc")
    second = vault("attach", image, library / "Attachments", "Instagram DQx1abc")

    assert first["link"] == "[[Graveyard Killer/Attachments/Instagram DQx1abc.jpg]]"
    assert second["link"] == "[[Graveyard Killer/Attachments/Instagram DQx1abc 2.jpg]]"
    assert Path(first["path"]).read_bytes() == b"\xff\xd8 jpeg"


def test_trash_moves_a_note_to_the_vaults_trash(library: Path) -> None:
    made = vault("create", library / "Entries", "Duplicate", stdin={"set": {"Nota": "Duplicato di x"}})

    out = vault("trash", made["path"])

    assert not Path(made["path"]).exists()
    assert Path(out["path"]) == library.parent / ".trash" / "Duplicate.md"


def test_check_finds_the_vault_of_a_library(library: Path) -> None:
    out = vault("check", library)

    assert out == {"path": str(library.resolve()), "exists": True,
                   "vault": str(library.parent.resolve()), "vault_name": "My Vault"}
    assert vault("check", library.parent.parent)["vault"] is None


def test_new_file_and_new_folder_never_overwrite(library: Path) -> None:
    base = library / "Graveyard Killer.base"

    vault("new-file", base, stdin={"text": "views:\n  - type: table\n"})
    out = vault("new-file", base, stdin={"text": "other"}, ok=False)
    vault("new-folder", library / "Attachments")

    assert "already exists" in out["error"]
    assert base.read_text(encoding="utf-8") == "views:\n  - type: table\n"
    assert (library / "Attachments").is_dir()


def test_a_missing_note_is_an_error(library: Path) -> None:
    out = vault("read", library / "Entries" / "Nope.md", ok=False)

    assert out["error"].startswith("no such file")


# ---------- Only inside the vault ----------
# The agent runs the script without asking, and a post's text may try to steer it.


def test_no_write_outside_a_vault(library: Path, tmp_path: Path) -> None:
    outside = tmp_path / "profile.md"
    outside.write_text("keep me\n", encoding="utf-8")

    vault("update", outside, stdin={"body": "changed"}, ok=False)
    vault("new-file", tmp_path / "new.md", ok=False)
    vault("trash", outside, ok=False)
    vault("move-text", outside, library / "Already read.md", stdin={"text": "keep me"}, ok=False)

    assert outside.read_text(encoding="utf-8") == "keep me\n"
    assert not (tmp_path / "new.md").exists()


def test_no_write_in_the_vaults_own_folders_or_to_other_kinds_of_file(library: Path) -> None:
    root = library.parent

    assert "error" in vault("new-file", root / ".obsidian" / "plugins.md", ok=False)
    assert "error" in vault("new-folder", root / ".trash" / "x", ok=False)
    assert "error" in vault("new-file", library / "run.sh", ok=False)
    assert "error" in vault("new-file", root, ok=False)
    assert vault("new-file", library / "Library.base")["path"].endswith("Library.base")


def test_a_link_inside_the_vault_to_a_file_outside_is_refused(library: Path, tmp_path: Path) -> None:
    outside = tmp_path / "elsewhere.md"
    outside.write_text("keep me\n", encoding="utf-8")
    (library / "Entries" / "Sneaky.md").symlink_to(outside)

    vault("update", library / "Entries" / "Sneaky.md", stdin={"body": "changed"}, ok=False)

    assert outside.read_text(encoding="utf-8") == "keep me\n"


def test_out_is_only_a_new_jsonl_file(library: Path, tmp_path: Path) -> None:
    taken = tmp_path / "taken.jsonl"
    taken.write_text("keep me\n", encoding="utf-8")

    vault("list", library / "Entries", "--out", taken, ok=False)
    vault("list", library / "Entries", "--out", tmp_path / "list.txt", ok=False)

    assert taken.read_text(encoding="utf-8") == "keep me\n"
    assert vault("list", library / "Entries", "--out", tmp_path / "new.jsonl")["count"] == 0


def test_attach_copies_only_an_image(library: Path, tmp_path: Path) -> None:
    secret = tmp_path / "id_rsa"
    secret.write_text("PRIVATE\n", encoding="utf-8")

    vault("attach", secret, library / "Attachments", "Post", ok=False)

    assert not (library / "Attachments").exists() or not any((library / "Attachments").iterdir())
