from pathlib import Path
from tika import parser as tika_parser
import ezdxf

class FileParser:
    @staticmethod
    def parse(file_path: Path) -> str:
        ext = file_path.suffix.lower()
        
        try:
            # Spezialfall: CAD (wird von Tika nicht nativ als Text extrahiert)
            if ext == ".dxf":
                doc = ezdxf.readfile(file_path)
                text_lines = []
                # Extrahiere alle Text-Elemente aus dem CAD-Modellraum
                for entity in doc.modelspace().query("TEXT MTEXT"):
                    if entity.dxftype() == "TEXT":
                        text_lines.append(entity.dxf.text)
                    elif entity.dxftype() == "MTEXT":
                        text_lines.append(entity.text)
                return "\n".join(text_lines)
            
            # Universeller Parser für TXT, MS Office, LibreOffice & OpenOffice
            else:
                # Tika parst die Datei und gibt ein Dict mit ['content'] und ['metadata'] zurück
                parsed_data = tika_parser.from_file(str(file_path))
                text_content = parsed_data.get("content", "")
                
                if text_content:
                    # Tika fügt oft viele Leerzeilen am Anfang/Ende hinzu, die wir säubern
                    return text_content.strip()
                return ""
                
        except Exception as e:
            print(f"Fehler beim Parsen von {file_path.name} ({ext}): {e}")
            return ""

    @staticmethod
    def generate_summary(text: str) -> str:
        if not text:
            return ""
        # Hier bleibt deine bestehende LLM-Zusammenfassung
        return f"Zusammenfassung: {text[:100]}..."