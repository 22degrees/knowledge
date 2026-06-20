from pathlib import Path
from app.core.config import settings
from app.database.state_db import StateDB
from app.services.parser import FileParser

class IndexerService:
    def __init__(self):
        self.db = StateDB(settings.STATE_DB_PATH)
        # self.chroma_client = ... (Hier dein ChromaDB Client Setup)

    def extract_metadata(self, file_path: Path, root_path: Path, allowed_departments: list) -> dict:
        relative_path = file_path.relative_to(root_path.parent)
        parts = [part.lower() for part in relative_path.parent.parts if part and part != "."]

        return {
            "source_path": str(file_path),
            "filename": file_path.name,
            "file_extension": file_path.suffix.lower(),
            "departments": ", ".join(allowed_departments), # Berechtigungen anhängen
            "keywords": ", ".join(parts) # Pfad-Segmente als Keywords
        }

    def sync_folders(self):
        supported_extensions = {
            # Text
            ".txt", 
            # MS Office
            ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt",
            # LibreOffice / OpenOffice
            ".odt", ".ods", ".odp",
            # CAD
            ".dxf"
        }
        scanned_files = set()

        for path_str, departments in settings.INDEX_CONFIG.items():
            root_path = Path(path_str)
            if not root_path.exists():
                print(f"Pfad existiert nicht: {root_path}")
                continue

            for file_path in root_path.rglob("*"):
                if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                    scanned_files.add(str(file_path))
                    
                    should_update, file_hash = self.db.should_update(file_path)

                    if should_update and file_hash: # Nur verarbeiten, wenn Hash-Berechnung erfolgreich war
                        print(f"Verarbeite (Änderung erkannt via Hash): {file_path}")
                        
                        # Text extrahieren & Summary generieren
                        text_content = FileParser.parse(file_path)
                        summary = FileParser.generate_summary(text_content)
                        
                        # Metadaten erweitern (Wir packen den Hash direkt in die Chroma-Metadaten!)
                        metadata = self.extract_metadata(file_path, root_path, departments)
                        metadata["file_hash"] = file_hash 
                        
                        # Upsert ChromaDB
                        self._upsert_to_chroma(str(file_path), text_content, summary, metadata)
                        
                        # State in SQLite mit dem bereits berechneten Hash aktualisieren
                        self.db.update_state(file_path, file_hash)

        # Bereinigung: Dateien entfernen, die im echten Verzeichnis gelöscht wurden
        stored_files = self.db.get_all_paths()
        deleted_files = stored_files - scanned_files
        for dead_path in deleted_files:
            print(f"Entferne gelöschte Datei aus Index: {dead_path}")
            self._delete_from_chroma(dead_path)
            self.db.remove_state(dead_path)

    def _upsert_to_chroma(self, doc_id: str, text: str, summary: str, metadata: dict):
        """Hier fließt der Text und das Summary-Embedding in die ChromaDB."""
        # Du kannst zwei getrennte Dokumente anlegen: 
        # 1. Den Volltext (ggf. gechunkt) -> id: doc_id + "#chunk_x"
        # 2. Die Zusammenfassung -> id: doc_id + "#summary"
        pass

    def _delete_from_chroma(self, doc_id: str):
        """Löscht alle Einträge zu dieser Datei aus ChromaDB."""
        # self.chroma_collection.delete(where={"source_path": doc_id})
        pass