import os

# Config options
ACTIVE_REPOSITORY = "json"  # Can be "json", or in the future "supabase", "firebase"

# File paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
JSON_DB_PATH = os.path.join(DATA_DIR, "checklists.json")

# History settings
# History retention in days
HISTORY_RETENTION_DAYS = 14

# Default categories if none specified
DEFAULT_CATEGORIES = ["Att göra", "Packning & Förskola", "Inköp", "Planering", "Övrigt"]
