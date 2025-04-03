"""
XML to Markdown converter - processes structured XML tax documents into Markdown format.
Handles sections, subsections, paragraphs, tables, and other tax code elements.
"""

import re
import sys

from bs4 import BeautifulSoup
from lxml import etree


def convert_xml_to_markdown(xml_file, markdown_file):
    """
    Convert XML file to Markdown using BeautifulSoup for HTML-like elements.
    """
    print(f"Loading XML file: {xml_file}")
    try:
        with open(xml_file, "r", encoding="utf-8") as file:
            xml_data = file.read()
            print(f"Successfully loaded {len(xml_data)} bytes")
    except Exception as e:
        print(f"Error loading XML file: {e}")
        return

    print("Parsing XML...")
    try:
        # Parse with recover option to handle namespace issues
        parser = etree.XMLParser(recover=True)
        root = etree.fromstring(xml_data.encode("utf-8"), parser)
    except Exception as e:
        print(f"Error parsing XML: {e}")
        return

    print("Converting to Markdown...")

    # Convert XML to markdown
    markdown_content = process_xml_tree(root)

    # Clean up excessive newlines and spacing
    markdown_content = re.sub(r"\n{3,}", "\n\n", markdown_content)

    # Clean up leading/trailing whitespace on each line
    lines = markdown_content.split("\n")
    markdown_content = "\n".join([line.strip() for line in lines])

    # Remove blank lines before headings
    markdown_content = re.sub(r"\n\n(#+\s)", r"\n\1", markdown_content)

    # Remove excessive spaces
    markdown_content = re.sub(r" {2,}", " ", markdown_content)

    print(f"Writing Markdown to: {markdown_file}")
    try:
        with open(markdown_file, "w", encoding="utf-8") as file:
            file.write(markdown_content)
        print("Conversion completed successfully!")
    except Exception as e:
        print(f"Error writing Markdown file: {e}")


# Include all the helper functions from main.py
def should_process_children(element):
    """Determine if we should process children of this element separately"""
    tag = get_tag_name(element)
    # These elements handle their children internally
    skip_children_tags = [
        "section",
        "subsection",
        "paragraph",
        "subparagraph",
        "table",
        "list",
        "note",
        "notes",
    ]
    return tag not in skip_children_tags


def process_xml_tree(element, level=0):
    """
    Process XML tree and convert to Markdown.
    Only processes certain elements directly, others are handled by their parents.
    """
    if element is None:
        return ""

    # Get markdown for this element
    result = element_to_markdown(element, level)

    # Only process children for elements that don't already handle their children
    if should_process_children(element):
        for child in element:
            child_result = process_xml_tree(child, level + 1)
            if child_result:
                result += child_result

    return result


def element_to_markdown(element, level=0):
    """
    Convert a single XML element to markdown based on its tag.
    """
    if element is None:
        return ""

    tag = get_tag_name(element)
    text = element.text or ""

    # Skip empty elements
    if not text.strip() and tag not in [
        "section",
        "subsection",
        "paragraph",
        "subparagraph",
        "table",
        "list",
        "title",
        "note",
        "notes",
    ]:
        return ""

    result = ""

    # Handle different element types
    if (
        tag == "title"
        and element.getparent() is not None
        and get_tag_name(element.getparent()) == "uscDoc"
    ):
        # Document title
        num = get_child_text(element, "num")
        heading = get_child_text(element, "heading")

        if num:
            result += f"# {num}\n\n"
        if heading:
            result += f"# {heading}\n\n"

    elif tag == "section":
        # Section headers
        num = get_child_text(element, "num")
        heading = get_child_text(element, "heading")

        # Process content
        content = ""
        for child in element:
            child_tag = get_tag_name(child)
            if child_tag not in ["num", "heading"]:
                child_result = process_xml_tree(child, level + 1)
                if child_result:
                    content += child_result

        header = ""
        if num:
            header += num + " "
        if heading:
            header += heading

        if header:
            result += f"\n## {header}\n\n"

        result += content

    elif tag == "subsection":
        # Subsection headers
        num = get_child_text(element, "num")
        heading = get_child_text(element, "heading")

        # Process content
        content = ""
        for child in element:
            child_tag = get_tag_name(child)
            if child_tag not in ["num", "heading"]:
                child_result = process_xml_tree(child, level + 1)
                if child_result:
                    content += child_result

        header = ""
        if num:
            header += num + " "
        if heading:
            header += heading

        if header:
            result += f"\n### {header}\n\n"

        result += content

    elif tag == "paragraph":
        # Paragraphs with numbering
        num = get_child_text(element, "num")
        content_text = get_child_text(element, "content")

        # Process additional content
        additional_content = ""
        for child in element:
            child_tag = get_tag_name(child)
            if child_tag not in ["num", "content"]:
                child_result = process_xml_tree(child, level + 1)
                if child_result:
                    additional_content += child_result

        if num:
            result += f"**{num}** "
        if content_text:
            result += f"{content_text} "

        result += additional_content.strip()
        if result.strip():
            result += "\n"

    elif tag == "subparagraph":
        # Subparagraphs
        num = get_child_text(element, "num")
        content_text = get_child_text(element, "content")

        # Process additional content
        additional_content = ""
        for child in element:
            child_tag = get_tag_name(child)
            if child_tag not in ["num", "content"]:
                child_result = process_xml_tree(child, level + 1)
                if child_result:
                    additional_content += child_result

        if num:
            result += f"  - **{num}** "
        if content_text:
            result += f"{content_text} "

        result += additional_content.strip()
        if result.strip():
            result += "\n"

    elif tag == "p":
        # Regular paragraphs
        if text.strip():
            result += text.strip() + " "

    elif tag == "content" or tag == "chapeau":
        # Content blocks
        if text.strip():
            result += text.strip() + " "

    elif tag == "table":
        # Convert tables to markdown tables
        table_content = table_to_markdown(element)
        if table_content:
            result += table_content + "\n"

    elif tag == "note" or tag == "notes":
        # Notes become blockquotes
        note_content = ""

        # Process note heading separately
        heading = get_child_text(element, "heading")
        if heading:
            note_content += f"> **{heading}**\n"

        if text.strip():
            # Add blockquote to each line
            lines = [f"> {line}" for line in text.strip().split("\n")]
            note_content += "\n".join(lines) + "\n"

        # Process additional content
        for child in element:
            child_tag = get_tag_name(child)
            if child_tag not in ["heading"]:
                child_result = process_xml_tree(child, level + 1)
                if child_result:
                    child_lines = child_result.split("\n")
                    blockquote_lines = []
                    for line in child_lines:
                        if line.strip():
                            blockquote_lines.append(f"> {line}")
                    if blockquote_lines:
                        note_content += "\n".join(blockquote_lines) + "\n"

        result += note_content

    elif tag == "ref":
        # References become links - no newlines
        href = element.get("href", "")
        if href and text.strip():
            result += f"[{text.strip()}]({href})"
        elif text.strip():
            result += f"*{text.strip()}*"

    elif tag == "list":
        # Handle lists
        list_content = convert_list(element)
        if list_content:
            result += list_content + "\n"

    elif tag in ["num", "heading"]:
        # Skip elements that are handled by their parents
        pass

    elif tag == "meta" or tag == "main":
        # Container elements - no direct markdown
        pass

    elif text.strip():
        # Any other element with text
        result += text.strip() + " "

    # Handle tail text (inline)
    if element.tail and element.tail.strip():
        result += element.tail.strip() + " "

    return result


def get_tag_name(element):
    """Get clean tag name without namespace."""
    tag = element.tag
    if "}" in tag:
        return tag.split("}")[1]
    return tag


def get_child_text(element, child_tag):
    """Get text from a child element with the given tag."""
    for child in element:
        if get_tag_name(child) == child_tag and child.text:
            return child.text.strip()
    return ""


def table_to_markdown(table_element):
    """Convert XML table to Markdown table."""
    # Convert to HTML first
    table_html = etree.tostring(table_element, encoding="unicode")

    # Parse with BeautifulSoup
    soup = BeautifulSoup(table_html, "html.parser")
    table = soup.find("table")

    if not table:
        return ""

    result = []

    # Process header
    headers = []
    thead = table.find("thead")
    if thead:
        for th in thead.find_all("th"):
            # Get all text from the th element
            header_text = th.get_text(strip=True)
            headers.append(header_text)

    if headers:
        result.append("| " + " | ".join(headers) + " |")
        result.append("| " + " | ".join(["---"] * len(headers)) + " |")

    # Process body
    tbody = table.find("tbody")
    if tbody:
        for tr in tbody.find_all("tr"):
            row = []
            for td in tr.find_all("td"):
                # Get all text from the td element
                cell_text = td.get_text(strip=True)
                row.append(cell_text)

            if row:
                result.append("| " + " | ".join(row) + " |")

    return "\n".join(result)


def convert_list(list_element):
    """Convert XML list to Markdown list."""
    result = []

    # Process list items
    for item in list_element.xpath(".//item"):
        item_text = ""
        if item.text:
            item_text += item.text.strip()

        # Get all content within the item
        for content in item.xpath(".//content"):
            if content.text:
                item_text += " " + content.text.strip()

        if item_text:
            result.append(f"* {item_text}")

    return "\n".join(result)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 2:
        xml_file = sys.argv[1]
        markdown_file = sys.argv[2]
    else:
        xml_file = "data/usc26.xml"
        markdown_file = "data/usc26.md"
    convert_xml_to_markdown(xml_file, markdown_file)
