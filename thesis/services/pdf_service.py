import re
import unicodedata

import fitz  # PyMuPDF
import tiktoken


class PDFService:
    MAX_TOKENS_PER_CHUNK: int = 2000
    ENCODING_NAME: str = 'cl100k_base'

    @staticmethod
    def extract_text(pdf_path: str) -> str:
        """Extract all readable text from a PDF using PyMuPDF."""
        doc = fitz.open(pdf_path)
        pages = []
        for page in doc:
            pages.append(page.get_text())
        doc.close()
        return '\n'.join(pages)

    @staticmethod
    def clean_text(raw: str) -> str:
        """Remove non-printable characters and normalise whitespace."""
        # Remove non-printable characters (keep printable ASCII + common unicode)
        cleaned = ''.join(
            ch for ch in raw
            if unicodedata.category(ch)[0] != 'C' or ch in ('\n', '\t')
        )
        # Normalise multiple spaces to single space (but preserve newlines)
        cleaned = re.sub(r'[ \t]+', ' ', cleaned)
        # Normalise multiple newlines to double newline
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        return cleaned.strip()

    @staticmethod
    def chunk_text(text: str) -> list:
        """Split text into chunks of at most MAX_TOKENS_PER_CHUNK tokens."""
        enc = tiktoken.get_encoding(PDFService.ENCODING_NAME)
        tokens = enc.encode(text)
        max_tokens = PDFService.MAX_TOKENS_PER_CHUNK

        chunks = []
        for i in range(0, len(tokens), max_tokens):
            chunk_tokens = tokens[i:i + max_tokens]
            chunk_text = enc.decode(chunk_tokens)
            chunks.append(chunk_text)

        return chunks if chunks else [text]

    @classmethod
    def process(cls, pdf_path: str) -> list:
        """Convenience method: extract → clean → chunk. Returns list of text chunks."""
        raw = cls.extract_text(pdf_path)
        cleaned = cls.clean_text(raw)
        return cls.chunk_text(cleaned)
