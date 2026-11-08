import io
from pathlib import Path
from typing import Union, BinaryIO, Optional


def extract_pdf_text(source: Union[Path, str, BinaryIO, bytes]) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise RuntimeError("Install pypdf to parse PDF resumes: pip install pypdf") from e

    if isinstance(source, (str, Path)):
        reader = PdfReader(str(source))
    elif isinstance(source, bytes):
        reader = PdfReader(io.BytesIO(source))
    else:
        reader = PdfReader(source)

    return "\n".join((page.extract_text() or "") for page in reader.pages)


def extract_docx_text(source: Union[Path, str, BinaryIO, bytes]) -> str:
    try:
        import docx
    except ImportError:
        # Fallback if docx not installed
        return ""

    if isinstance(source, (str, Path)):
        doc = docx.Document(str(source))
    elif isinstance(source, bytes):
        doc = docx.Document(io.BytesIO(source))
    else:
        doc = docx.Document(source)

    full_text = []
    for para in doc.paragraphs:
        if para.text:
            full_text.append(para.text)
    for table in doc.tables:
        for row in table.rows:
            row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if row_text:
                full_text.append(" | ".join(row_text))
    return "\n".join(full_text)


def extract_resume_text(source: Union[Path, str, BinaryIO, bytes], filename: Optional[str] = None) -> str:
    """Extract raw text from PDF, DOCX, or TXT file."""
    name = (filename or (str(source) if isinstance(source, (str, Path)) else "")).lower()
    
    if name.endswith(".docx"):
        return extract_docx_text(source)
    elif name.endswith(".txt"):
        if isinstance(source, (str, Path)):
            return Path(source).read_text(encoding="utf-8", errors="ignore")
        elif isinstance(source, bytes):
            return source.decode("utf-8", errors="ignore")
        elif hasattr(source, "read"):
            data = source.read()
            if isinstance(data, bytes):
                return data.decode("utf-8", errors="ignore")
            return str(data)
        return ""
    else:
        # Default to PDF parsing
        try:
            return extract_pdf_text(source)
        except Exception:
            # Fallback to docx attempt
            try:
                return extract_docx_text(source)
            except Exception:
                return ""


def resume_summary(text: str) -> dict:
    from .ai_agent import analyze_resume
    return analyze_resume(text)
