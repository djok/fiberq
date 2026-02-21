"""
FiberQ Zitadel OIDC Authentication for QGIS Desktop.

Implements Device Authorization Flow (RFC 8628) which is ideal for
desktop/CLI applications – user opens a browser link, enters a code,
and the plugin receives the token automatically.

Token is cached in QSettings and refreshed automatically.
"""

import json
import os
import ssl
import time
import configparser
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional

try:
    from qgis.PyQt.QtCore import QSettings, QTimer, QUrl
    from qgis.PyQt.QtGui import QDesktopServices
    from qgis.PyQt.QtWidgets import (
        QDialog, QVBoxLayout, QLabel, QPushButton, QMessageBox, QHBoxLayout,
        QLineEdit, QApplication
    )
    HAS_QT = True
except ImportError:
    HAS_QT = False


_SETTINGS_ORG = "FiberQ"
_SETTINGS_APP = "FiberQ"
_TOKEN_KEY = "server/access_token"
_REFRESH_KEY = "server/refresh_token"
_EXPIRY_KEY = "server/token_expiry"
_USER_SUB_KEY = "server/user_sub"
_USER_EMAIL_KEY = "server/user_email"


def _plugin_root_dir():
    return os.path.dirname(os.path.dirname(__file__))


def _load_zitadel_config():
    plugin_dir = _plugin_root_dir()
    cfg_path = os.path.join(plugin_dir, "config.ini")
    if not os.path.exists(cfg_path):
        raise RuntimeError(f"config.ini not found at {cfg_path}")

    cp = configparser.ConfigParser()
    cp.read(cfg_path, encoding="utf-8")
    if "server" not in cp:
        raise RuntimeError("Missing [server] section in config.ini")

    s = cp["server"]
    domain = s.get("zitadel_domain", "").strip()
    client_id = s.get("zitadel_client_id", "").strip()

    if not domain or not client_id:
        raise RuntimeError(
            "Zitadel auth not configured.\n"
            "Set zitadel_domain and zitadel_client_id in config.ini [server] section."
        )

    return {"domain": domain, "client_id": client_id}


def _http_post(url: str, data: dict, timeout: int = 15) -> dict:
    ctx = ssl.create_default_context()
    encoded = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(
        url, data=encoded,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "FiberQ-QGIS-Plugin/1.0",
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        raise RuntimeError(f"Auth error {e.code}: {body}") from e


class ZitadelAuth:
    """Manages OIDC authentication with Zitadel Cloud."""

    def __init__(self):
        self._cfg = None
        self._access_token = None
        self._refresh_token = None
        self._expiry = 0.0

    def _ensure_config(self):
        if self._cfg is None:
            self._cfg = _load_zitadel_config()

    @property
    def domain(self) -> str:
        self._ensure_config()
        return self._cfg["domain"]

    @property
    def client_id(self) -> str:
        self._ensure_config()
        return self._cfg["client_id"]

    @property
    def token_endpoint(self) -> str:
        return f"https://{self.domain}/oauth/v2/token"

    @property
    def device_auth_endpoint(self) -> str:
        return f"https://{self.domain}/oauth/v2/device_authorization"

    # ------------------------------------------------------------------
    # Token persistence
    # ------------------------------------------------------------------

    def _load_cached_token(self):
        if not HAS_QT:
            return
        s = QSettings(_SETTINGS_ORG, _SETTINGS_APP)
        self._access_token = s.value(_TOKEN_KEY, None)
        self._refresh_token = s.value(_REFRESH_KEY, None)
        try:
            self._expiry = float(s.value(_EXPIRY_KEY, 0))
        except (ValueError, TypeError):
            self._expiry = 0.0

    def _save_token(self, access_token: str, refresh_token: Optional[str],
                    expires_in: int):
        self._access_token = access_token
        if refresh_token:
            self._refresh_token = refresh_token
        self._expiry = time.time() + expires_in - 60  # 60s safety margin

        if HAS_QT:
            s = QSettings(_SETTINGS_ORG, _SETTINGS_APP)
            s.setValue(_TOKEN_KEY, access_token)
            if refresh_token:
                s.setValue(_REFRESH_KEY, refresh_token)
            s.setValue(_EXPIRY_KEY, str(self._expiry))

    def _clear_token(self):
        self._access_token = None
        self._refresh_token = None
        self._expiry = 0.0
        if HAS_QT:
            s = QSettings(_SETTINGS_ORG, _SETTINGS_APP)
            s.remove(_TOKEN_KEY)
            s.remove(_REFRESH_KEY)
            s.remove(_EXPIRY_KEY)
            s.remove(_USER_SUB_KEY)
            s.remove(_USER_EMAIL_KEY)

    # ------------------------------------------------------------------
    # Token access
    # ------------------------------------------------------------------

    def get_token(self) -> Optional[str]:
        if self._access_token is None:
            self._load_cached_token()

        if self._access_token and time.time() < self._expiry:
            return self._access_token

        # Try refresh
        if self._refresh_token:
            try:
                self._do_refresh()
                return self._access_token
            except Exception:
                pass

        return None

    def is_authenticated(self) -> bool:
        return self.get_token() is not None

    # ------------------------------------------------------------------
    # Refresh token flow
    # ------------------------------------------------------------------

    def _do_refresh(self):
        self._ensure_config()
        result = _http_post(self.token_endpoint, {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "refresh_token": self._refresh_token,
        })
        self._save_token(
            result["access_token"],
            result.get("refresh_token"),
            result.get("expires_in", 3600),
        )

    # ------------------------------------------------------------------
    # Device Authorization Flow
    # ------------------------------------------------------------------

    def start_device_flow(self) -> dict:
        self._ensure_config()
        result = _http_post(self.device_auth_endpoint, {
            "client_id": self.client_id,
            "scope": "openid profile email "
                     "urn:zitadel:iam:org:project:roles "
                     "offline_access",
        })
        return result

    def poll_device_flow(self, device_code: str, interval: int = 5,
                         timeout: int = 300) -> bool:
        self._ensure_config()
        deadline = time.time() + timeout

        while time.time() < deadline:
            time.sleep(interval)
            try:
                result = _http_post(self.token_endpoint, {
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "client_id": self.client_id,
                    "device_code": device_code,
                })
                self._save_token(
                    result["access_token"],
                    result.get("refresh_token"),
                    result.get("expires_in", 3600),
                )
                return True
            except RuntimeError as e:
                err_str = str(e).lower()
                if "authorization_pending" in err_str or "slow_down" in err_str:
                    continue
                if "expired" in err_str or "denied" in err_str:
                    return False
                continue

        return False

    def logout(self):
        self._clear_token()


# Singleton
_auth_instance = None


def get_auth() -> ZitadelAuth:
    global _auth_instance
    if _auth_instance is None:
        _auth_instance = ZitadelAuth()
    return _auth_instance


# ------------------------------------------------------------------
# Login Dialog (Qt)
# ------------------------------------------------------------------

if HAS_QT:

    class LoginDialog(QDialog):
        """Device Authorization Flow dialog for QGIS."""

        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("FiberQ – Sign In")
            self.setMinimumWidth(420)
            self._auth = get_auth()
            self._timer = None
            self._device_code = None
            self._poll_interval = 5
            self._success = False

            layout = QVBoxLayout(self)

            self.lbl_status = QLabel("Click 'Sign In' to start authentication.")
            self.lbl_status.setWordWrap(True)
            layout.addWidget(self.lbl_status)

            self.lbl_code = QLabel("")
            self.lbl_code.setStyleSheet("font-size: 24px; font-weight: bold; "
                                        "padding: 10px; text-align: center;")
            self.lbl_code.setVisible(False)
            layout.addWidget(self.lbl_code)

            self.lbl_url = QLabel("")
            self.lbl_url.setWordWrap(True)
            self.lbl_url.setOpenExternalLinks(True)
            self.lbl_url.setVisible(False)
            layout.addWidget(self.lbl_url)

            btn_row = QHBoxLayout()
            self.btn_login = QPushButton("Sign In")
            self.btn_login.clicked.connect(self._start_flow)
            btn_row.addWidget(self.btn_login)

            self.btn_copy = QPushButton("Copy Code")
            self.btn_copy.setVisible(False)
            self.btn_copy.clicked.connect(self._copy_code)
            btn_row.addWidget(self.btn_copy)

            self.btn_cancel = QPushButton("Cancel")
            self.btn_cancel.clicked.connect(self.reject)
            btn_row.addWidget(self.btn_cancel)

            layout.addLayout(btn_row)

        def _start_flow(self):
            try:
                result = self._auth.start_device_flow()
            except Exception as e:
                QMessageBox.critical(self, "Auth Error", str(e))
                return

            user_code = result.get("user_code", "")
            verification_uri = result.get("verification_uri_complete",
                                          result.get("verification_uri", ""))
            self._device_code = result.get("device_code", "")
            self._poll_interval = result.get("interval", 5)

            self.lbl_status.setText(
                "Open the link below in your browser and enter the code:"
            )
            self.lbl_code.setText(user_code)
            self.lbl_code.setVisible(True)
            self.lbl_url.setText(
                f'<a href="{verification_uri}">{verification_uri}</a>'
            )
            self.lbl_url.setVisible(True)
            self.btn_copy.setVisible(True)
            self.btn_login.setEnabled(False)

            # Open browser
            try:
                QDesktopServices.openUrl(QUrl(verification_uri))
            except Exception:
                pass

            # Start polling
            self._timer = QTimer(self)
            self._timer.timeout.connect(self._poll_once)
            self._timer.start(self._poll_interval * 1000)

        def _poll_once(self):
            try:
                result = _http_post(self._auth.token_endpoint, {
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "client_id": self._auth.client_id,
                    "device_code": self._device_code,
                })
                # Success
                self._auth._save_token(
                    result["access_token"],
                    result.get("refresh_token"),
                    result.get("expires_in", 3600),
                )
                self._success = True
                if self._timer:
                    self._timer.stop()
                self.lbl_status.setText("Authenticated successfully!")
                self.lbl_code.setVisible(False)
                self.lbl_url.setVisible(False)
                self.btn_copy.setVisible(False)
                QTimer.singleShot(1000, self.accept)

            except RuntimeError as e:
                err_str = str(e).lower()
                if "authorization_pending" in err_str or "slow_down" in err_str:
                    return  # Keep polling
                if "expired" in err_str or "denied" in err_str:
                    if self._timer:
                        self._timer.stop()
                    self.lbl_status.setText("Authentication expired or denied. Try again.")
                    self.btn_login.setEnabled(True)
                    return
                # Unknown error, keep polling
                return

        def _copy_code(self):
            try:
                QApplication.clipboard().setText(self.lbl_code.text())
            except Exception:
                pass

        def was_successful(self) -> bool:
            return self._success


def open_login_dialog(iface) -> bool:
    """Open the login dialog. Returns True if login was successful."""
    auth = get_auth()

    # Already authenticated?
    if auth.is_authenticated():
        reply = QMessageBox.question(
            iface.mainWindow(),
            "FiberQ Auth",
            "You are already signed in.\nSign out and sign in again?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.No:
            return True
        auth.logout()

    dlg = LoginDialog(iface.mainWindow())
    dlg.exec_()
    return dlg.was_successful()


def open_logout_dialog(iface):
    """Sign out and clear cached token."""
    auth = get_auth()
    auth.logout()
    QMessageBox.information(iface.mainWindow(), "FiberQ", "Signed out successfully.")
