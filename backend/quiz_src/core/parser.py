import os
from pathlib import Path

class ReportParser:
    def __init__(self, file_path):
        self.file_path = Path(file_path)

    def get_raw_text(self):
        """Detects file type and extracts text."""
        suffix = self.file_path.suffix.lower()
        
        if suffix == ".txt":
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif suffix == ".pdf":
            # For the demo, we'll assume you might use a library like pypdf
            # For now, let's return a placeholder or simple logic
            return "PDF Extraction Logic goes here"
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

    def clean_text(self, text):
        """Basic cleaning to help the LLM and Vector DB."""
        # Remove excessive whitespace/newlines that mess up embeddings
        return " ".join(text.split())