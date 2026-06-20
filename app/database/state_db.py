import sqlite3
import hashlib
from pathlib import Path

class StateDB:
    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS file_states (
                    filepath TEXT PRIMARY KEY,
                    file_hash TEXT,
                    file_size INTEGER
                )
            """)
            conn.commit()

    @staticmethod
    def calculate_md5(filepath: Path) -> str:
        """Berechnet den MD5-Hash einer Datei effizient in Chunks."""
        hasher = hashlib.md5()
        try:
            with open(filepath, "rb") as f:
                # 8192 Bytes Chunks lesen, um RAM zu schonen
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            print(f"Fehler beim Hashen von {filepath}: {e}")
            return ""

    def should_update(self, filepath: Path) -> tuple[bool, str]:
        """
        Prüft anhand von Größe und Hash, ob ein Update nötig ist.
        Gibt (True/False, berechneter_hash) zurück.
        """
        stat = filepath.stat()
        current_size = stat.st_size

        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT file_hash, file_size FROM file_states WHERE filepath = ?", 
                (str(filepath),)
            )
            row = cursor.fetchone()
            
            if row is None:
                # Datei ist komplett neu -> Hash berechnen und True zurückgeben
                return True, self.calculate_md5(filepath)
            
            saved_hash, saved_size = row
            
            # Fast-Check: Wenn die Größe anders ist, hat sich das File definitiv geändert
            if current_size != saved_size:
                return True, self.calculate_md5(filepath)
            
            # Slow-Check: Wenn Größe gleich, aber Inhalt unsicher (z.B. nach Umzug)
            current_hash = self.calculate_md5(filepath)
            if current_hash != saved_hash:
                return True, current_hash
                
            return False, current_hash

    def update_state(self, filepath: Path, file_hash: str):
        stat = filepath.stat()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO file_states (filepath, file_hash, file_size)
                VALUES (?, ?, ?)
                """,
                (str(filepath), file_hash, stat.st_size)
            )
            conn.commit()

    def remove_state(self, filepath: str):
        with self._get_connection() as conn:
            conn.execute("DELETE FROM file_states WHERE filepath = ?", (filepath,))
            conn.commit()

    def get_all_paths(self) -> set:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT filepath FROM file_states")
            return {row[0] for row in cursor.fetchall()}