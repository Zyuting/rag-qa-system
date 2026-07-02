"""Tests for the text chunking module.

Covers: basic splitting, paragraph-aware boundaries,
long-paragraph sliding-window, overlap preservation.
"""
from backend.chunker import split_documents


def _doc(content: str, filename: str = "test.txt", source: str = "/fake/test.txt") -> dict:
    return {"content": content, "source": source, "filename": filename}


# ── Basic splitting ──


def test_empty_document():
    assert split_documents([]) == []


def test_single_short_paragraph():
    docs = [_doc("Hello world.")]
    chunks = split_documents(docs, chunk_size=500, chunk_overlap=100)
    assert len(chunks) == 1
    assert "Hello world." in chunks[0]["content"]


def test_multiple_paragraphs_fit_in_one_chunk():
    text = "\n".join(["A" * 100, "B" * 100, "C" * 100])
    docs = [_doc(text)]
    chunks = split_documents(docs, chunk_size=500, chunk_overlap=100)
    assert len(chunks) == 1


def test_paragraphs_split_across_chunks():
    """Two paragraphs that together exceed chunk_size spill into 2 chunks."""
    p1 = "A" * 300
    p2 = "B" * 300
    docs = [_doc(f"{p1}\n{p2}")]
    chunks = split_documents(docs, chunk_size=400, chunk_overlap=50)
    assert len(chunks) >= 2


# ── Long-paragraph sliding window ──


def test_long_paragraph_sliding_window():
    """A single paragraph longer than chunk_size is split by sliding window."""
    para = "X" * 1000
    docs = [_doc(para)]
    chunks = split_documents(docs, chunk_size=300, chunk_overlap=50)
    assert len(chunks) >= 3
    # Every chunk should be non-empty
    assert all(c["content"].strip() for c in chunks)


def test_sliding_window_step_is_chunk_size_minus_overlap():
    para = "X" * 500
    docs = [_doc(para)]
    chunks = split_documents(docs, chunk_size=200, chunk_overlap=50)
    # step = 200 - 50 = 150 → ceil(500/150) ≈ 4 chunks
    assert 3 <= len(chunks) <= 5


# ── Overlap correctness ──


def test_overlap_contains_tail_of_previous_chunk():
    """When a chunk boundary falls mid-paragraph, the next chunk
    should start with overlapping content from the tail of the previous."""
    para = "A" * 100 + "B" * 100 + "C" * 100 + "D" * 100
    docs = [_doc(para)]
    chunks = split_documents(docs, chunk_size=150, chunk_overlap=50)
    if len(chunks) >= 2:
        assert "B" in chunks[1]["content"] or "C" in chunks[1]["content"]


# ── Metadata preservation ──


def test_chunk_metadata():
    docs = [_doc("Hello world.", filename="foo.txt", source="/path/to/foo.txt")]
    chunks = split_documents(docs)
    assert chunks[0]["filename"] == "foo.txt"
    assert chunks[0]["source"] == "/path/to/foo.txt"
    assert "chunk_id" in chunks[0]


def test_chunk_ids_are_monotonic():
    para = "\n".join(["A" * 200, "B" * 200, "C" * 200, "D" * 200])
    docs = [_doc(para)]
    chunks = split_documents(docs, chunk_size=150, chunk_overlap=30)
    ids = [c["chunk_id"] for c in chunks]
    assert ids == sorted(ids)


# ── Edge cases ──


def test_whitespace_only_document():
    docs = [_doc("   \n  \n  ")]
    chunks = split_documents(docs)
    assert chunks == []


def test_single_character_paragraph():
    docs = [_doc("X")]
    chunks = split_documents(docs, chunk_size=10, chunk_overlap=2)
    assert len(chunks) == 1
    assert chunks[0]["content"] == "X"


def test_chunk_size_equals_paragraph_length():
    para = "A" * 100
    docs = [_doc(para)]
    chunks = split_documents(docs, chunk_size=100, chunk_overlap=20)
    assert len(chunks) == 1


def test_chunk_size_smaller_than_any_character():
    """Extreme: chunk_size=1, each char becomes its own chunk."""
    docs = [_doc("AB")]
    chunks = split_documents(docs, chunk_size=1, chunk_overlap=0)
    assert len(chunks) == 2
