from pathlib import Path
from typing import TYPE_CHECKING

from toolbox.mcp_installer.python_package_installer import uvx_path
from toolbox.store.callbacks.callback import Callback

if TYPE_CHECKING:
    from toolbox.store.installation_context import InstallationContext


class GoogleSheetsMCPAuthCallback(Callback):
    def on_mcp_obj_init_finished(self, context: "InstallationContext"):
        context.mcp.json_body["command"] = str(uvx_path())

    def on_install_init(self, context: "InstallationContext", json_body: dict):
        print("""
Configure OAuth Consent Screen: In GCP Console https://console.cloud.google.com/ -> "APIs & Services" -> "OAuth consent screen".
Select "External", fill required info, add scopes (.../auth/spreadsheets, .../auth/drive), add test users if needed.
Create OAuth Client ID: In GCP Console -> "APIs & Services" -> "Credentials". "+ CREATE CREDENTIALS" -> "OAuth client ID" -> Type: Desktop app.
Name it. "CREATE". Download JSON.

Go to https://console.developers.google.com/apis/api/drive.googleapis.com/overview?project=687028089248 and enable the drive API
Go to https://console.cloud.google.com/apis/library/sheets.googleapis.com?project=hazel-sky-470511-s6 and enable the sheets API

""")

        oauth_credentials_path = input("Insert path to OAuth credentials JSON file: ")
        token_path = (
            Path.home() / ".google-sheets-mcp-token-dir" / "token.json"
        ).resolve()
        token_path.parent.mkdir(parents=True, exist_ok=True)

        json_body["env"] = {
            "CREDENTIALS_PATH": str(oauth_credentials_path),
            "TOKEN_PATH": str(token_path),
        }
