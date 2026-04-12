from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHROMEDRIVER_EXE = PROJECT_ROOT / "bin" / "chromedriver.exe"
CHROME_EXE = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
CHROME_USER_DATA_DIR = PROJECT_ROOT / "chrome_profile"
TARGET_URL = "https://i.mi.com/note/#/"
REMOTE_DEBUGGING_PORT = 9222
