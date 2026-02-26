import tempfile
from pathlib import Path

from n0conflict.conflict import ConflictBlock, has_conflicts, parse_conflicts

SIMPLE_CONFLICT = """\
def greet(name):
<<<<<<< HEAD
    return f"Hello, {name}!"
=======
    return f"Hi there, {name}!"
>>>>>>> feature/friendly-greeting
"""

DOUBLE_CONFLICT = """\
<<<<<<< HEAD
x = 1
=======
x = 2
>>>>>>> other-branch

<<<<<<< HEAD
y = 10
=======
y = 20
>>>>>>> other-branch
"""


class TestParseConflicts:
    def test_finds_one_block(self):
        blocks = parse_conflicts(SIMPLE_CONFLICT)
        assert len(blocks) == 1

    def test_finds_two_blocks(self):
        blocks = parse_conflicts(DOUBLE_CONFLICT)
        assert len(blocks) == 2

    def test_ours_content(self):
        block = parse_conflicts(SIMPLE_CONFLICT)[0]
        assert 'return f"Hello, {name}!"' in block.ours

    def test_theirs_content(self):
        block = parse_conflicts(SIMPLE_CONFLICT)[0]
        assert 'return f"Hi there, {name}!"' in block.theirs

    def test_ours_label(self):
        block = parse_conflicts(SIMPLE_CONFLICT)[0]
        assert block.ours_label == "HEAD"

    def test_theirs_label(self):
        block = parse_conflicts(SIMPLE_CONFLICT)[0]
        assert block.theirs_label == "feature/friendly-greeting"

    def test_raw_round_trips(self):
        """raw should appear verbatim in the original content."""
        block = parse_conflicts(SIMPLE_CONFLICT)[0]
        assert block.raw in SIMPLE_CONFLICT

    def test_no_conflicts_returns_empty(self):
        assert parse_conflicts("def foo(): pass\n") == []

    def test_line_numbers(self):
        block = parse_conflicts(SIMPLE_CONFLICT)[0]
        assert block.start == 2   # second line of the file
        assert block.end == 6


class TestHasConflicts:
    def test_clean_file(self, tmp_path: Path):
        f = tmp_path / "clean.py"
        f.write_text("x = 1\n")
        assert has_conflicts(f) is False

    def test_conflicted_file(self, tmp_path: Path):
        f = tmp_path / "dirty.py"
        f.write_text(SIMPLE_CONFLICT)
        assert has_conflicts(f) is True

    def test_missing_file(self, tmp_path: Path):
        assert has_conflicts(tmp_path / "nonexistent.py") is False
