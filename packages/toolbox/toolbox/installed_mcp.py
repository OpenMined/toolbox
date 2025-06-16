import json
import sqlite3
import urllib

from pathlib import Path
from pydantic import BaseModel
from toolbox.store import STORE, get_default_setting

HOME = Path.home()
INSTALLED_HEADERS = ["NAME", "CLIENT", "DEPLOYMENT", "READ ACCESS", "WRITE ACCESS", "MODEL", "HOST", "MANAGED BY", "PROXY", "VERIFIED", "CLIENT CONFIG"]


class InstalledMCP(BaseModel):
    name: str
    client: str
    read_access: list[str]
    write_access: list[str]
    model: str | None = None
    host: str
    managed_by: str
    proxy: str | None = None
    verified: bool
    json_body: dict | None = None
    deployment_method: str
    
    @property
    def client_config_file(self) -> str:
        if self.client == "claude":
            return "[1]"
        else:
            raise ValueError(f"Client {self.client} not supported")
    
    def format_as_tabulate_row(self) -> list[str]:
        return [
            self.name,
            self.client,
            self.deployment_method,
            ",\n".join(self.read_access),
            ",\n".join(self.write_access),
            self.model if self.model is not None else "",
            self.host,
            self.managed_by,
            self.proxy if self.proxy is not None else "",
            "✓" if self.verified else "",
            self.client_config_file
        ]
        
        
    @classmethod
    def from_cli_args(cls, name:str, client:str, read_access:list[str] | None=None, write_access:list[str] | None=None,
                      model:str | None=None, host:str|None=None, managed_by:str|None=None, proxy:str|None=None,
                      deployment_method:str|None=None, secret_requests:list["RequestedSecret"]=None):
        
        if name not in STORE:
            raise ValueError(f"{name} not found in store, store has entries: {list(STORE.keys())}")
        
        if read_access is None:
            read_access = get_default_setting(name, client, "read_access")
        if write_access is None:
            write_access = get_default_setting(name, client, "write_access")
        if model is None:
            model = get_default_setting(name, client, "model")
        if host is None:
            host = get_default_setting(name, client, "host")
        if managed_by is None:
            managed_by = get_default_setting(name, client, "managed_by")
        if proxy is None:
            proxy = get_default_setting(name, client, "proxy")
        
        verified = get_default_setting(name, client, "verified")
            
        if deployment_method is None:
            deployment_method = get_default_setting(name, client, "deployment_method")
            
        json_bodies_for_client_for_deployment_method = STORE[name]["json_bodies_for_client_for_deployment_method"]
        if "all" in json_bodies_for_client_for_deployment_method:
            jsons_bodies_for_deployment_methods = json_bodies_for_client_for_deployment_method["all"]
        elif client in json_bodies_for_client_for_deployment_method:
            jsons_bodies_for_deployment_methods = json_bodies_for_client_for_deployment_method[client]
        else:
            raise ValueError(f"{client} is not a valid client, valid clients are: {list(json_bodies_for_client_for_deployment_method.keys())}")
    
        if deployment_method not in jsons_bodies_for_deployment_methods:
            raise ValueError(f"The chosen deployment method is not available for {client}")
        
        json_body = jsons_bodies_for_deployment_methods[deployment_method]
        
        for secret_request in secret_requests:
            secret_request.add_to_json_body(json_body)
            
        
        return cls(
            name=name,
            client=client,
            read_access=read_access,
            write_access=write_access,
            model=model,
            host=host,
            managed_by=managed_by,
            proxy=proxy,
            verified=verified,
            json_body=json_body,
            deployment_method=deployment_method,
        )
    @classmethod
    def from_db_row(cls, row: sqlite3.Row):
        row = dict(row)
        row['client'] = json.loads(row['client'])
        row['read_access'] = json.loads(row['read_access'])
        row['write_access'] = json.loads(row['write_access'])
        row['json_body'] = json.loads(row['json_body'])
        row['deployment_method'] = row['deployment_method']
        return cls(**row)
    
    
def create_clickable_file_link(file_path, link_text="LINK"):
    abs_path = urllib.parse.quote(file_path)
    file_url = f"file://{abs_path}"
    return file_url
    