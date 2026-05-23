"""
utils/helpers.py — Shared utility helpers
==========================================
Small, reusable functions used across the codebase.
Keeping them here prevents duplication and keeps route files clean.
"""

import os
from pathlib import Path
from fastapi import HTTPException


def chroma_is_ready(chroma_dir: str) -> bool:
    """
    Return True if the ChromaDB directory exists and contains at least one file.
    Used as a pre-flight guard before any RAG endpoint runs.
    """
    return (
        os.path.exists(chroma_dir)
        and os.path.isdir(chroma_dir)
        and any(Path(chroma_dir).iterdir())
    )


def require_vectorstore(chroma_dir: str) -> None:
    """
    Raise HTTP 400 if no regulation has been indexed yet.
    Call this at the top of any route that needs the vectorstore.
    """
    if not chroma_is_ready(chroma_dir):
        raise HTTPException(
            status_code=400,
            detail=(
                "No regulation indexed yet. "
                "Upload a regulation PDF via POST /regulation/upload first."
            ),
        )


class FileAdapter:
    """
    Minimal adapter that mimics the Streamlit UploadedFile interface
    (attributes: .name, method: .read()) expected by detect_gaps() and
    other pipeline functions that were originally written for Streamlit.

    This lets us pass a saved-to-disk file into those functions without
    modifying the underlying pipeline code at all.
    """

    def __init__(self, path: Path):
        self.name = path.name
        self._path = path

    def read(self) -> bytes:
        return self._path.read_bytes()
