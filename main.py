from fastmcp import FastMCP
from apscheduler.schedulers.background import BackgroundScheduler
from app.core.config import settings
from app.services.indexer import IndexerService

# Instanziere den FastMCP Server
mcp = FastMCP("Knowledge-MCP-Server")
indexer_service = IndexerService()
scheduler = BackgroundScheduler()

def run_indexing_pipeline():
    try:
        indexer_service.sync_folders()
    except Exception as e:
        print(f"Fehler während des Indexierungs-Intervalls: {e}")

# --- FastMCP Lifecycles ---

@mcp.on_startup
def init_background_tasks():
    print("Starte Background-Scheduler für Datei-Indexierung...")
    # Intervall aus Pydantic Settings laden
    interval = settings.SCAN_INTERVAL_SECONDS
    
    # Task registrieren und sofort einmal anstoßen
    scheduler.add_job(run_indexing_pipeline, 'interval', seconds=interval)
    scheduler.start()
    
    # Erster manueller Trigger beim Start (optional, läuft asynchron an)
    scheduler.trigger_job(scheduler.get_jobs()[0].id)

@mcp.on_shutdown
def shutdown_background_tasks():
    print("Stoppe Background-Scheduler...")
    scheduler.shutdown()

# --- Hier folgen deine regulären MCP Tools / Prompts ---
@mcp.tool()
def search_knowledge(query: str, department: str = None) -> str:
    """Durchsucht das Firmenwissen in der ChromaDB."""
    # Hier greift dein MCP auf die ChromaDB zu und filtert 
    # optional nach der übergebenen Abteilung (Metadaten-Filter)
    return f"Suchergebnisse für '{query}'"

if __name__ == "__main__":
    mcp.run()