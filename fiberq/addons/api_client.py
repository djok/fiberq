"""
FiberQ API Client – HTTP communication with the FiberQ server.

Uses urllib (stdlib) to avoid external dependencies in the QGIS plugin.
All methods return parsed JSON or raise RuntimeError on failure.
"""

import json
import os
import ssl
import urllib.error
import urllib.parse
import urllib.request
import configparser
from typing import Optional


def _plugin_root_dir():
    return os.path.dirname(os.path.dirname(__file__))


def _load_server_config():
    plugin_dir = _plugin_root_dir()
    cfg_path = os.path.join(plugin_dir, "config.ini")
    if not os.path.exists(cfg_path):
        raise RuntimeError(f"config.ini not found at {cfg_path}")

    cp = configparser.ConfigParser()
    cp.read(cfg_path, encoding="utf-8")

    if "server" not in cp:
        raise RuntimeError("Missing [server] section in config.ini")

    s = cp["server"]
    api_url = s.get("api_url", "").strip()
    if not api_url:
        raise RuntimeError(
            "api_url is not configured in config.ini [server] section.\n"
            "Set it to your FiberQ server address, e.g. https://fiberq.company.com"
        )

    return {
        "api_url": api_url.rstrip("/"),
        "zitadel_domain": s.get("zitadel_domain", "").strip(),
        "zitadel_client_id": s.get("zitadel_client_id", "").strip(),
    }


class FiberQApiClient:
    """Stateless HTTP client for the FiberQ REST API."""

    def __init__(self, base_url: Optional[str] = None, token: Optional[str] = None):
        if base_url:
            self.base_url = base_url.rstrip("/")
        else:
            cfg = _load_server_config()
            self.base_url = cfg["api_url"]
        self.token = token
        self._ssl_ctx = ssl.create_default_context()

    def set_token(self, token: str):
        self.token = token

    # ------------------------------------------------------------------
    # Low-level HTTP
    # ------------------------------------------------------------------

    def _request(self, method: str, path: str, body=None,
                 query: Optional[dict] = None, timeout: int = 30) -> dict:
        url = f"{self.base_url}{path}"
        if query:
            url += "?" + urllib.parse.urlencode(
                {k: v for k, v in query.items() if v is not None}
            )

        headers = {"User-Agent": "FiberQ-QGIS-Plugin/1.0"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=data, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, context=self._ssl_ctx, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8")
                if not raw:
                    return {}
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            err_body = ""
            try:
                err_body = e.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            raise RuntimeError(
                f"API error {e.code} {method} {path}: {err_body}"
            ) from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"Connection error: {e.reason}") from e

    def get(self, path: str, query: Optional[dict] = None, timeout: int = 30) -> dict:
        return self._request("GET", path, query=query, timeout=timeout)

    def post(self, path: str, body=None, timeout: int = 30) -> dict:
        return self._request("POST", path, body=body, timeout=timeout)

    def put(self, path: str, body=None, timeout: int = 30) -> dict:
        return self._request("PUT", path, body=body, timeout=timeout)

    def delete(self, path: str, timeout: int = 30) -> dict:
        return self._request("DELETE", path, timeout=timeout)

    # ------------------------------------------------------------------
    # File upload (multipart)
    # ------------------------------------------------------------------

    def upload_file(self, path: str, file_path: str,
                    field_name: str = "file", timeout: int = 120) -> dict:
        import mimetypes
        boundary = "----FiberQBoundary"
        filename = os.path.basename(file_path)
        content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"

        with open(file_path, "rb") as f:
            file_data = f.read()

        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode("utf-8") + file_data + f"\r\n--{boundary}--\r\n".encode("utf-8")

        url = f"{self.base_url}{path}"
        headers = {
            "User-Agent": "FiberQ-QGIS-Plugin/1.0",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, context=self._ssl_ctx, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            err_body = ""
            try:
                err_body = e.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            raise RuntimeError(f"Upload error {e.code}: {err_body}") from e

    def download_file(self, path: str, dest_path: str, timeout: int = 120):
        url = f"{self.base_url}{path}"
        headers = {"User-Agent": "FiberQ-QGIS-Plugin/1.0"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        req = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req, context=self._ssl_ctx, timeout=timeout) as resp:
                with open(dest_path, "wb") as f:
                    while True:
                        chunk = resp.read(65536)
                        if not chunk:
                            break
                        f.write(chunk)
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"Download error {e.code}") from e

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    def health(self) -> dict:
        return self.get("/health", timeout=10)

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def me(self) -> dict:
        return self.get("/auth/me")

    # ------------------------------------------------------------------
    # Projects
    # ------------------------------------------------------------------

    def list_projects(self) -> list:
        return self.get("/projects/")

    def create_project(self, name: str, description: str = "") -> dict:
        return self.post("/projects/", {"name": name, "description": description})

    def get_project(self, project_id: int) -> dict:
        return self.get(f"/projects/{project_id}")

    # ------------------------------------------------------------------
    # Fiber Plan – Splice Closures
    # ------------------------------------------------------------------

    def list_closures(self, project_id: Optional[int] = None) -> list:
        q = {"project_id": project_id} if project_id else None
        return self.get("/fiber-plan/closures", query=q)

    def create_closure(self, data: dict) -> dict:
        return self.post("/fiber-plan/closures", data)

    def list_trays(self, closure_id: int) -> list:
        return self.get(f"/fiber-plan/closures/{closure_id}/trays")

    def create_tray(self, closure_id: int, data: dict) -> dict:
        return self.post(f"/fiber-plan/closures/{closure_id}/trays", data)

    # ------------------------------------------------------------------
    # Fiber Plan – Splices
    # ------------------------------------------------------------------

    def list_splices(self, tray_id: Optional[int] = None,
                     closure_id: Optional[int] = None) -> list:
        q = {}
        if tray_id is not None:
            q["tray_id"] = tray_id
        if closure_id is not None:
            q["closure_id"] = closure_id
        return self.get("/fiber-plan/splices", query=q or None)

    def create_splice(self, data: dict) -> dict:
        return self.post("/fiber-plan/splices", data)

    def update_splice(self, splice_id: int, data: dict) -> dict:
        return self.put(f"/fiber-plan/splices/{splice_id}", data)

    # ------------------------------------------------------------------
    # Fiber Plan – Patches
    # ------------------------------------------------------------------

    def list_patches(self, element_fid: Optional[int] = None) -> list:
        q = {"element_fid": element_fid} if element_fid else None
        return self.get("/fiber-plan/patches", query=q)

    def create_patch(self, data: dict) -> dict:
        return self.post("/fiber-plan/patches", data)

    # ------------------------------------------------------------------
    # Fiber Plan – Tracing
    # ------------------------------------------------------------------

    def trace_fiber(self, element_fid: int, port_number: int) -> dict:
        return self.get(f"/fiber-plan/trace/{element_fid}/{port_number}", timeout=60)

    def list_paths(self, project_id: Optional[int] = None) -> list:
        q = {"project_id": project_id} if project_id else None
        return self.get("/fiber-plan/paths", query=q)

    # ------------------------------------------------------------------
    # Work Orders
    # ------------------------------------------------------------------

    def list_work_orders(self, project_id: Optional[int] = None,
                         status: Optional[str] = None) -> list:
        q = {}
        if project_id is not None:
            q["project_id"] = project_id
        if status:
            q["status"] = status
        return self.get("/work-orders/", query=q or None)

    def create_work_order(self, data: dict) -> dict:
        return self.post("/work-orders/", data)

    def update_work_order(self, wo_id: int, data: dict) -> dict:
        return self.put(f"/work-orders/{wo_id}", data)

    def assign_work_order(self, wo_id: int, assigned_to_sub: str) -> dict:
        return self.post(f"/work-orders/{wo_id}/assign",
                         {"assigned_to_sub": assigned_to_sub})

    def change_work_order_status(self, wo_id: int, status: str) -> dict:
        return self.put(f"/work-orders/{wo_id}/status", {"status": status})

    def my_work_orders(self) -> list:
        return self.get("/work-orders/my")

    # ------------------------------------------------------------------
    # Work Order Items
    # ------------------------------------------------------------------

    def list_work_order_items(self, wo_id: int) -> list:
        return self.get(f"/work-orders/{wo_id}/items")

    def create_work_order_item(self, wo_id: int, data: dict) -> dict:
        return self.post(f"/work-orders/{wo_id}/items", data)

    # ------------------------------------------------------------------
    # SMR Reports
    # ------------------------------------------------------------------

    def list_smr_reports(self, wo_id: int) -> list:
        return self.get(f"/smr-reports/", query={"work_order_id": wo_id})

    def create_smr_report(self, data: dict) -> dict:
        return self.post("/smr-reports/", data)

    # ------------------------------------------------------------------
    # Photos
    # ------------------------------------------------------------------

    def upload_photo(self, file_path: str, related_type: str,
                     related_id: int, caption: str = "") -> dict:
        # Use multipart upload
        return self.upload_file(
            f"/photos/upload?related_type={related_type}"
            f"&related_id={related_id}&caption={urllib.parse.quote(caption)}",
            file_path, field_name="file"
        )

    # ------------------------------------------------------------------
    # Sync
    # ------------------------------------------------------------------

    def sync_upload(self, gpkg_path: str, project_id: int) -> dict:
        return self.upload_file(
            f"/sync/upload?project_id={project_id}",
            gpkg_path, field_name="file", timeout=300
        )

    def sync_download(self, project_id: int, dest_path: str):
        self.download_file(f"/sync/download/{project_id}", dest_path, timeout=300)
