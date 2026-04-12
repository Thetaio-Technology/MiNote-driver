import subprocess

from .config import CHROME_EXE, CHROME_USER_DATA_DIR, REMOTE_DEBUGGING_PORT, TARGET_URL


def open_mi_cloud() -> None:
    if not CHROME_EXE.exists():
        raise FileNotFoundError(f"Chrome executable not found: {CHROME_EXE}")

    CHROME_USER_DATA_DIR.mkdir(exist_ok=True)

    subprocess.Popen(
        [
            str(CHROME_EXE),
            f"--user-data-dir={CHROME_USER_DATA_DIR}",
            "--profile-directory=Default",
            f"--remote-debugging-port={REMOTE_DEBUGGING_PORT}",
            TARGET_URL,
        ]
    )
