from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError


@dataclass
class DocumentTool:
    def _read_text(self, file_path: str) -> dict[str, object]:
        target = Path(file_path)
        if not target.exists():
            return {"status": "error", "message": f"File not found: {file_path}"}

        if target.suffix.lower() == ".pdf":
            try:
                reader = PdfReader(str(target))
                content = "\n".join(page.extract_text() or "" for page in reader.pages)
            except (OSError, PdfReadError, ValueError) as exc:
                return {"status": "error", "message": f"Unable to read file: {exc}"}
        else:
            try:
                content = target.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                return {"status": "error", "message": f"Unable to read file: {exc}"}

        if not content.strip():
            return {"status": "error", "message": "File is empty or contains no extractable text."}

        return {
            "status": "ok",
            "file_path": str(target),
            "extension": target.suffix.lower(),
            "chars": len(content),
            "words": len(content.split()),
            "content": content,
        }

    def read_pdf(self, file_path: str) -> dict[str, object]:
        if Path(file_path).suffix.lower() != ".pdf":
            return {"status": "error", "message": "The selected file is not a PDF."}
        return self.read_document(file_path)

    def read_document(self, file_path: str) -> dict[str, object]:
        result = self._read_text(file_path)
        if result["status"] != "ok":
            return result

        content = str(result["content"])
        preview = content[:500].strip().replace("\n", " ")
        return {
            "status": "ok",
            "file_path": result["file_path"],
            "extension": result["extension"],
            "chars": result["chars"],
            "words": result["words"],
            "preview": preview,
        }

    def summarize_pdf(self, file_path: str) -> dict[str, object]:
        if Path(file_path).suffix.lower() != ".pdf":
            return {"status": "error", "message": "The selected file is not a PDF."}
        return self.summarize_document(file_path)

    def summarize_document(self, file_path: str) -> dict[str, object]:
        result = self._read_text(file_path)
        if result["status"] != "ok":
            return result

        content = str(result["content"])
        cleaned = re.sub(r"\s+", " ", content).strip()
        sentences = re.split(r"(?<=[.!?])\s+", cleaned)
        summary_sentences = []
        for sentence in sentences[:3]:
            if sentence.strip():
                summary_sentences.append(sentence.strip())

        if not summary_sentences:
            summary = cleaned[:220]
        else:
            summary = " ".join(summary_sentences)

        return {
            "status": "summarized",
            "file_path": result["file_path"],
            "extension": result["extension"],
            "words": result["words"],
            "summary": summary[:500],
        }
