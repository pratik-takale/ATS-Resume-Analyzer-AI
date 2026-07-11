import io
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph
from bs4 import BeautifulSoup


def html_to_text(html: str) -> str:
    """Convert HTML to plain text."""
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text("\n")


def generate_combined_pdf(html_docs: dict[str, str]) -> bytes:
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()

    story = []

    for title, html in html_docs.items():

        story.append(Paragraph(f"<b>{title}</b>", styles["Heading1"]))

        text = html_to_text(html)

        for line in text.split("\n"):
            line = line.strip()
            if line:
                story.append(Paragraph(line, styles["BodyText"]))

    doc.build(story)

    pdf = buffer.getvalue()

    buffer.close()

    return pdf