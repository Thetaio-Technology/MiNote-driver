from __future__ import annotations

import base64
import ctypes
import json
import shutil
import sqlite3
import tempfile
from pathlib import Path

import win32crypt
from Crypto.Cipher import AES


def _copy_locked_file(src: Path, dst: Path) -> None:
    """Copy a file that may be locked by another process (e.g. Chrome)."""
    kernel32 = ctypes.windll.kernel32
    # Open with FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE
    GENERIC_READ = 0x80000000
    FILE_SHARE_ALL = 0x07
    OPEN_EXISTING = 3
    FILE_ATTRIBUTE_NORMAL = 0x80

    h = kernel32.CreateFileW(
        str(src), GENERIC_READ, FILE_SHARE_ALL, None, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, None
    )
    if h == -1:
        raise PermissionError(f"Cannot open locked file: {src}")
    try:
        with open(dst, "wb") as f:
            buf = ctypes.create_string_buffer(65536)
            while True:
                read = ctypes.c_ulong(0)
                kernel32.ReadFile(h, buf, len(buf), ctypes.byref(read), None)
                if read.value == 0:
                    break
                f.write(buf.raw[: read.value])
    finally:
        kernel32.CloseHandle(h)


def _get_aes_key(local_state_path: Path) -> bytes:
    with open(local_state_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    encrypted_key = base64.b64decode(data["os_crypt"]["encrypted_key"])
    encrypted_key = encrypted_key[5:]  # strip DPAPI prefix
    return win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]


def _decrypt_cookie_value(encrypted: bytes, key: bytes) -> str:
    if encrypted[:3] != b"v10":
        raise ValueError(f"Unexpected cookie encryption prefix: {encrypted[:3]}")
    nonce = encrypted[3:15]
    ciphertext_and_tag = encrypted[15:]
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    plaintext = cipher.decrypt_and_verify(
        ciphertext_and_tag[:-16], ciphertext_and_tag[-16:]
    )
    # Chrome stores a 32-byte binary prefix before the actual cookie value
    if len(plaintext) > 32:
        try:
            return plaintext[32:].decode("utf-8")
        except UnicodeDecodeError:
            return plaintext.decode("utf-8", errors="replace")
    return plaintext.decode("utf-8")


def _get_cookies_via_cdp(domain: str = ".mi.com") -> dict[str, str]:
    """Extract cookies from a running Chrome via CDP remote debugging."""
    import json
    import urllib.request

    try:
        pages = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=2).read())
    except Exception:
        return {}

    target = None
    for p in pages:
        if "i.mi.com" in p.get("url", ""):
            target = p
            break
    if not target:
        return {}

    import subprocess
    # Use chrome devtools protocol via simple HTTP
    ws_url = target.get("webSocketDebuggerUrl")
    if not ws_url:
        return {}

    try:
        import websockets
        import asyncio
    except ImportError:
        return {}

    async def _fetch():
        async with websockets.connect(ws_url, max_size=5 * 1024 * 1024) as ws:
            await ws.send(json.dumps({"id": 1, "method": "Network.getAllCookies"}))
            resp = json.loads(await ws.recv())
            cookies = {}
            for c in resp.get("result", {}).get("cookies", []):
                cdomain = c.get("domain", "")
                if domain in cdomain or cdomain.endswith(domain):
                    cookies[c["name"]] = c["value"]
            return cookies

    try:
        return asyncio.run(_fetch())
    except Exception:
        return {}


def get_cookies(profile_dir: Path, domain: str = ".mi.com") -> dict[str, str]:
    local_state = profile_dir / "Local State"
    cookies_db = profile_dir / "Default" / "Network" / "Cookies"

    if not cookies_db.exists():
        raise FileNotFoundError(f"Cookie database not found: {cookies_db}")
    if not local_state.exists():
        raise FileNotFoundError(f"Local State not found: {local_state}")

    aes_key = _get_aes_key(local_state)

    # Try to copy DB to temp file. If locked by Chrome, fall back to CDP.
    tmp_path = Path(tempfile.mktemp(suffix=".db"))
    use_tmp = False
    try:
        shutil.copy2(cookies_db, tmp_path)
        use_tmp = True
    except PermissionError:
        try:
            _copy_locked_file(cookies_db, tmp_path)
            use_tmp = True
        except PermissionError:
            pass

    if not use_tmp:
        # DB locked by Chrome — extract cookies via CDP remote debugging
        cookies = _get_cookies_via_cdp(domain)
        if cookies:
            return cookies
        raise PermissionError(
            "Cookie database is locked by Chrome and CDP fallback failed. "
            "Close Chrome or ensure remote debugging port 9222 is available."
        )

    try:
        conn = sqlite3.connect(str(tmp_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, encrypted_value FROM cookies WHERE host_key LIKE ?",
            (f"%{domain}%",),
        )
        cookies: dict[str, str] = {}
        for name, encrypted_value in cursor.fetchall():
            if encrypted_value and len(encrypted_value) > 15:
                try:
                    cookies[name] = _decrypt_cookie_value(encrypted_value, aes_key)
                except Exception:
                    pass
        conn.close()
    finally:
        tmp_path.unlink(missing_ok=True)

    return cookies
