import markdown


def smart_pygmented_markdown(text, flatpages=None, page=None):
    """
    Render Markdown text to HTML, similarly to Flask-Flatpages'
    renderer, except we store the markdown instance on the page.
    """
    extensions = flatpages.config('markdown_extensions') if flatpages else []
    if not extensions:
        extensions = ['codehilite']
    md = markdown.Markdown(extensions=extensions, output_format='html')
    page.md = md
    page.pages = flatpages
    return md.convert(text)
