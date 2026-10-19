"""Read CV on the user's computer; only generic competencies leave this module."""
from pathlib import Path
import re
from src.monica_match import COMPETENCIES, norm

def read_cv(path: Path) -> str:
    path = Path(path).expanduser().resolve(strict=True)
    if not path.is_file() or path.stat().st_size > 8_000_000:
        raise ValueError("CV must be a file no larger than 8 MB")
    ext = path.suffix.lower()
    if ext == ".txt":
        content = path.read_text(encoding="utf-8")
    elif ext == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("Install pypdf locally for PDF support") from exc
        reader = PdfReader(str(path))
        if len(reader.pages) > 50:
            raise ValueError("CV exceeds 50 pages")
        content = "\n".join(page.extract_text() or "" for page in reader.pages)
    elif ext == ".docx":
        try:
            from docx import Document
        except ImportError as exc:
            raise RuntimeError("Install python-docx locally for DOCX support") from exc
        doc = Document(str(path))
        content = "\n".join(p.text for p in doc.paragraphs)
    else:
        raise ValueError("Supported formats: PDF, DOCX, TXT")
    if len(content.strip()) < 100:
        raise ValueError("Unable to extract text from CV (scanned PDF may require OCR)")
    return content

def structured_profile(content: str) -> dict:
    value = norm(content)
    skills = [key for key, phrases in COMPETENCIES.items()
              if any(re.search(r"(?<!\w)"+re.escape(norm(p))+r"(?!\w)", value) for p in phrases)]
    return {"id":"monica","competencies":skills}
