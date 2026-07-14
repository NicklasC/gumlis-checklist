import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEPLOY_REPOSITORY = Path(
    os.environ.get("GUMLI_DEPLOY_REPOSITORY", PROJECT_ROOT.parent / "nicklasc.github.io")
)
DEPLOY_APP = DEPLOY_REPOSITORY / "gumlis-checklist"
PWA_TEMPLATES = PROJECT_ROOT / "pwa_templates"
