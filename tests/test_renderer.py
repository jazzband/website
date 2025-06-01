"""
Tests for the renderer module.

These tests cover Markdown rendering functionality.
"""

import markdown

from jazzband.renderer import smart_pygmented_markdown


def test_smart_pygmented_markdown_with_flatpages(mock_flatpages, mock_page):
    """Test smart_pygmented_markdown with flatpages config."""
    flatpages = mock_flatpages(["codehilite", "toc"])

    text = "# Test Heading\n\nThis is **bold** text."

    result = smart_pygmented_markdown(text, flatpages=flatpages, page=mock_page)

    # Should render as HTML (with id attribute from toc extension)
    assert "<h1" in result and "Test Heading</h1>" in result
    assert "<strong>bold</strong>" in result

    # Should set attributes on page
    assert hasattr(mock_page, "md")
    assert hasattr(mock_page, "pages")
    assert isinstance(mock_page.md, markdown.Markdown)
    assert mock_page.pages == flatpages


def test_smart_pygmented_markdown_without_flatpages(mock_page):
    """Test smart_pygmented_markdown without flatpages."""
    text = "# Test Heading\n\nThis is **bold** text."

    result = smart_pygmented_markdown(text, flatpages=None, page=mock_page)

    # Should render as HTML
    assert "<h1>Test Heading</h1>" in result
    assert "<strong>bold</strong>" in result

    # Should set attributes on page
    assert hasattr(mock_page, "md")
    assert hasattr(mock_page, "pages")
    assert isinstance(mock_page.md, markdown.Markdown)
    assert mock_page.pages is None


def test_smart_pygmented_markdown_with_empty_extensions(mock_flatpages, mock_page):
    """Test smart_pygmented_markdown when flatpages returns empty extensions."""
    flatpages = mock_flatpages([])  # Empty list

    text = "# Test Heading"

    result = smart_pygmented_markdown(text, flatpages=flatpages, page=mock_page)

    # Should use default codehilite extension and render as HTML
    assert "<h1" in result and "Test Heading</h1>" in result

    # Should have codehilite in the markdown instance extensions
    assert any("codehilite" in str(ext) for ext in mock_page.md.treeprocessors)


def test_smart_pygmented_markdown_code_highlighting(mock_page):
    """Test smart_pygmented_markdown handles code blocks."""
    text = """```python
def hello():
    print("Hello, World!")
```"""

    result = smart_pygmented_markdown(text, flatpages=None, page=mock_page)

    # Should render code block
    assert "<code>" in result or "<pre>" in result


def test_smart_pygmented_markdown_with_monkeypatch(mock_page, monkeypatch):
    """Test smart_pygmented_markdown with monkeypatch to control markdown behavior."""

    # Use monkeypatch to patch markdown.Markdown to return a controlled instance
    class MockMarkdown:
        def __init__(self, extensions=None, output_format="html"):
            self.extensions = extensions or []
            self.output_format = output_format
            self.treeprocessors = {"codehilite": "mock_processor"}

        def convert(self, text):
            return f"<p>Mocked conversion of: {text}</p>"

    monkeypatch.setattr("jazzband.renderer.markdown.Markdown", MockMarkdown)

    text = "# Test"
    result = smart_pygmented_markdown(text, flatpages=None, page=mock_page)

    # Should use our mocked markdown
    assert "Mocked conversion of: # Test" in result
    assert isinstance(mock_page.md, MockMarkdown)
