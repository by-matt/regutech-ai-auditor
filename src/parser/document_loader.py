"""Document ingestion and text/table extraction for regulatory dossiers."""

from dataclasses import dataclass, field
import io
import re
from typing import BinaryIO
from pypdf import PdfReader


@dataclass
class PageData:
    """Extracted content for an individual document page."""

    page_number: int
    text: str
    tables: list[list[list[str]]] = field(default_factory=list)


@dataclass
class DocumentContent:
    """Full extracted textual and tabular content of an ingested dossier."""

    filename: str
    pages: list[PageData]
    full_text: str

    def verify_substring(self, quote: str, case_sensitive: bool = False) -> tuple[bool, int]:
        """Verify whether an evidence quote exists as an exact substring.

        Normalizes internal whitespaces to avoid line-wrapping mismatches, but strictly
        requires lexical sequence fidelity.

        Returns:
            tuple[bool, int]: (is_verified, page_number_where_found)
        """
        if not quote or not quote.strip():
            return False, 0

        norm_quote = re.sub(r"\s+", " ", quote.strip())
        if not case_sensitive:
            norm_quote = norm_quote.lower()

        for page in self.pages:
            norm_page = re.sub(r"\s+", " ", page.text)
            if not case_sensitive:
                norm_page = norm_page.lower()

            if norm_quote in norm_page:
                return True, page.page_number

        return False, 0


class DocumentLoader:
    """Loads and extracts text and tables from PDFs or plaintext dossiers."""

    @staticmethod
    def load_pdf(file_input: str | bytes | BinaryIO, filename: str = "document.pdf") -> DocumentContent:
        """Parse PDF content into DocumentContent with page-level traceability."""
        pages: list[PageData] = []
        stream: BinaryIO

        if isinstance(file_input, str):
            with open(file_input, "rb") as f:
                content_bytes = f.read()
            stream = io.BytesIO(content_bytes)
        elif isinstance(file_input, bytes):
            stream = io.BytesIO(file_input)
        else:
            stream = file_input

        reader = PdfReader(stream)
        full_text_chunks: list[str] = []

        for idx, page in enumerate(reader.pages, start=1):
            extracted = page.extract_text() or ""
            pages.append(PageData(page_number=idx, text=extracted))
            full_text_chunks.append(extracted)

        return DocumentContent(
            filename=filename,
            pages=pages,
            full_text="\n\n--- PAGE BREAK ---\n\n".join(full_text_chunks),
        )

    @staticmethod
    def load_text(raw_text: str, filename: str = "dossier.txt") -> DocumentContent:
        """Parse raw text dossier into DocumentContent."""
        page = PageData(page_number=1, text=raw_text)
        return DocumentContent(
            filename=filename,
            pages=[page],
            full_text=raw_text,
        )

    @classmethod
    def load_bytes(cls, file_bytes: bytes, filename: str = "document.pdf") -> DocumentContent:
        """Parse in-memory bytes (PDF or plaintext) into DocumentContent."""
        if filename.lower().endswith(".txt"):
            return cls.load_text(file_bytes.decode("utf-8", errors="replace"), filename)
        return cls.load_pdf(file_bytes, filename)
