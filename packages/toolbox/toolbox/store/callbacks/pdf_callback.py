import json
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from toolbox.mcp_installer.python_package_installer import install_python_mcp
from toolbox.store.callbacks.callback import Callback

if TYPE_CHECKING:
    from toolbox.store.installation_context import InstallationContext
    from toolbox.installed_mcp import InstalledMCP


def ollama_installed() -> bool:
    """Check if Ollama is installed"""
    try:
        result = subprocess.run(["which", "ollama"], capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False


def ollama_running() -> bool:
    """Check if Ollama is running"""
    try:
        import requests

        response = requests.get("http://localhost:11434/api/version", timeout=2)
        return response.status_code == 200
    except Exception:
        return False


def poppler_installed() -> bool:
    """Check if poppler (pdftotext) is installed"""
    try:
        result = subprocess.run(["which", "pdftotext"], capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False


def start_ollama_and_pull_model():
    """Start Ollama and pull the required embedding model"""
    try:
        # Start Ollama in background
        subprocess.Popen(
            ["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

        # Wait a moment for startup
        import time

        time.sleep(3)

        # Pull the embedding model (same version as slack-mcp)
        result = subprocess.run(
            ["ollama", "pull", "nomic-embed-text:v1.5"], capture_output=True, text=True
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Failed to start Ollama or pull model: {e}")
        return False


class PDFMCPExternalDependencyCallback(Callback):
    def on_external_dependency_check(self, context: "InstallationContext"):
        """Check and guide installation of external dependencies"""
        missing_deps = []

        # Check poppler
        if not poppler_installed():
            missing_deps.append("poppler (for PDF text extraction)")

        # Check Ollama
        if not ollama_installed():
            missing_deps.append("Ollama (for embeddings)")

        if missing_deps:
            deps_str = ", ".join(missing_deps)
            input(f"""
PDF MCP requires the following external dependencies: {deps_str}

To install:
1. Poppler: brew install poppler (macOS) or sudo apt-get install poppler-utils (Linux)
2. Ollama: brew install ollama (macOS) or visit https://ollama.ai for other platforms

Press Enter once you've installed these dependencies to continue.""")

        # If Ollama is installed but not running, start it and pull model
        if ollama_installed() and not ollama_running():
            print("Starting Ollama and downloading embedding model...")
            if start_ollama_and_pull_model():
                print("✅ Ollama started and nomic-embed-text model downloaded")
            else:
                print(
                    "⚠️  Failed to start Ollama automatically. Please run 'ollama serve' and 'ollama pull nomic-embed-text' manually"
                )

    def on_external_dependency_status_check(self, mcp: "InstalledMCP") -> dict:
        """Check status of external dependencies"""
        status = {}

        # Check poppler
        if poppler_installed():
            status["poppler"] = "🟢"
        else:
            status["poppler"] = "🔴"

        # Check Ollama
        if ollama_running():
            status["ollama"] = "🟢"
        elif ollama_installed():
            status["ollama"] = "🟠 (not running)"
        else:
            status["ollama"] = "🔴"

        return status


class InstallPDFMCPCallback(Callback):
    def on_run_mcp(self, context: "InstallationContext", *args, **kwargs):
        """Install PDF MCP with proper configuration"""
        from toolbox.store.store_code import STORE_ELEMENTS
        from pathlib import Path

        # Set environment variables for directories
        context.context_settings["PDF_MCP_PORT"] = "8006"
        context.context_settings["DATA_DIR"] = str(Path.home() / ".pdf-mcp")
        context.context_settings["DOCUMENTS_DIR"] = str(Path.home() / "Documents")

        # Create the data directory
        data_dir = Path.home() / ".pdf-mcp"
        data_dir.mkdir(parents=True, exist_ok=True)

        store_element = STORE_ELEMENTS[context.current_app]
        install_python_mcp(store_element, context)

        # Trigger auto-loading after installation
        print(
            "📄 PDF MCP installed! Document loading will start automatically once the server is running."
        )
        print(
            "💡 Use 'get_loading_progress()' to track progress, or 'start_auto_loading()' to start manually."
        )


class PDFMCPInstallationSummaryCallback(Callback):
    def on_install_start(self, context: "InstallationContext"):
        """Show installation summary"""
        orange = "\033[33m"
        end = "\033[0m"
        end_bold = "\033[21m"
        bold = "\033[1m"
        print(f"""
{orange}{bold}PDF MCP Installation Summary:{end_bold}
This app provides semantic search capabilities for your PDF documents using local AI.

External dependencies required:
1. Poppler (pdftotext) - for fast PDF text extraction
2. Ollama - for local embedding generation (nomic-embed-text model)

Features:
• Fast semantic search through PDF documents
• Local processing (no data sent to external services)
• Pre-computed embeddings for instant queries
• Automatic document indexing from documents directory

Directory structure:
• Documents: ~/Documents/ (add PDFs here - your main Documents folder!)
• Data: ~/.pdf-mcp/ (embeddings cache and processed chunks)

Usage: Add PDFs to your main Documents folder, then ask Claude to search them!{end}
""")


class PDFMCPDataStatsCallback(Callback):
    def on_data_stats(self, mcp: "InstalledMCP") -> dict:
        """Get data stats"""
        # TODO, read app settings

        app_home = Path(mcp.settings.get("APP_HOME", Path.home() / ".pdf-mcp"))
        docs_dir = Path(mcp.settings.get("DOCUMENTS_DIR", Path.home() / "Documents"))
        chunks_file = app_home / "chunks.json"
        if not chunks_file.exists():
            n_chunks_str = "No Chunks found, is mcp still starting?"
            n_embedded_documents_str = "No Chunks found, is mcp still starting?"
        else:
            try:
                with open(chunks_file, "r") as f:
                    objs = json.load(f)
                    n_chunks_str = len(objs)
                    document_names = set(
                        x.get("document_name", None) for x in objs.values()
                    )
                    document_names.discard(None)
                    n_embedded_documents_str = len(document_names)
            except Exception:
                n_embedded_documents_str = f"Could not read {chunks_file}"
                n_chunks_str = f"Could not read {chunks_file}"

        try:
            n_pdf_files_str = len([f for f in docs_dir.glob("*.pdf") if f.is_file()])
        except Exception:
            n_pdf_files_str = f"Could not read {docs_dir}"

        return {
            "# Documents": n_pdf_files_str,
            "# Embedded Documents": n_embedded_documents_str,
            "# Chunks": n_chunks_str,
        }
