import subprocess
import shutil
import os
import sys
import hashlib


APP_ARCHIVE_HASH_PLACEHOLDER = "__APP_ARCHIVE_HASH__"


def add_app_archive_cache_buster(index_path, archive_path):
    """Tie the Python archive URL to its contents so existing PWAs fetch new code."""
    with open(archive_path, "rb") as archive_file:
        archive_hash = hashlib.sha256(archive_file.read()).hexdigest()[:16]

    with open(index_path, "r", encoding="utf-8") as index_file:
        index_html = index_file.read()

    if APP_ARCHIVE_HASH_PLACEHOLDER not in index_html:
        raise RuntimeError("index.html is missing the app archive hash placeholder")

    with open(index_path, "w", encoding="utf-8", newline="\n") as index_file:
        index_file.write(index_html.replace(APP_ARCHIVE_HASH_PLACEHOLDER, archive_hash))

    print(f"Versioned app.tar.gz with build hash {archive_hash}.")

def run_command(cmd, cwd=None):
    print(f"Executing: {cmd}")
    res = subprocess.run(cmd, cwd=cwd, shell=True, text=True, capture_output=True)
    if res.returncode != 0:
        print(f"Error executing command:\nSTDOUT: {res.stdout}\nSTDERR: {res.stderr}")
        sys.exit(res.returncode)
    print(res.stdout)
    return res.stdout

def main():
    source_dir = os.path.dirname(os.path.abspath(__file__))
    deploy_dir = os.path.abspath(os.path.join(source_dir, "..", "nicklasc.github.io", "gumlis-checklist"))
    templates_dir = os.path.join(source_dir, "pwa_templates")
    
    if not os.path.exists(templates_dir):
        print(f"Error: templates directory not found at {templates_dir}")
        sys.exit(1)
        
    print("\n--- 1. Compiling Web App with Flet Publish ---")
    
    # Dynamically resolve flet executable path if not in system PATH
    flet_cmd = "flet"
    if not shutil.which("flet"):
        scripts_dir = os.path.join(os.path.dirname(sys.executable), "Scripts")
        flet_exe = os.path.join(scripts_dir, "flet.exe")
        if os.path.exists(flet_exe):
            flet_cmd = f'"{flet_exe}"'
        else:
            # User specific fallback
            user_home = os.path.expanduser("~")
            custom_flet = os.path.join(user_home, "AppData", "Local", "Python", "pythoncore-3.14-64", "Scripts", "flet.exe")
            if os.path.exists(custom_flet):
                flet_cmd = f'"{custom_flet}"'
                
    publish_cmd = (
        f"{flet_cmd} publish src/main.py "
        f"--distpath \"{deploy_dir}\" "
        "--base-url /gumlis-checklist/ "
        "--assets assets"
    )
    run_command(publish_cmd, cwd=source_dir)
    
    print("\n--- 2. Restoring Custom Gumli PWA Container Templates ---")
    
    # Restore manifest.json
    print("Restoring manifest.json (App name & emerald/dark colors)...")
    shutil.copy2(
        os.path.join(templates_dir, "manifest.json"),
        os.path.join(deploy_dir, "manifest.json")
    )
    
    # Restore flutter_service_worker.js
    print("Restoring flutter_service_worker.js (Active persistent PWA caching)...")
    shutil.copy2(
        os.path.join(templates_dir, "flutter_service_worker.js"),
        os.path.join(deploy_dir, "flutter_service_worker.js")
    )
    
    # Restore index.html
    print("Restoring index.html (Metadata header titles)...")
    shutil.copy2(
        os.path.join(templates_dir, "index.html"),
        os.path.join(deploy_dir, "index.html")
    )
    add_app_archive_cache_buster(
        os.path.join(deploy_dir, "index.html"),
        os.path.join(deploy_dir, "app.tar.gz"),
    )
    
    # Restore favicon.png
    print("Restoring favicon.png...")
    shutil.copy2(
        os.path.join(templates_dir, "favicon.png"),
        os.path.join(deploy_dir, "favicon.png")
    )
    
    # Restore icons folder
    print("Restoring high-res custom green launcher icons...")
    dest_icons_dir = os.path.join(deploy_dir, "icons")
    if os.path.exists(dest_icons_dir):
        shutil.rmtree(dest_icons_dir)
    shutil.copytree(
        os.path.join(templates_dir, "icons"),
        dest_icons_dir
    )
    print("PWA container templates successfully restored!")
    
    print("\n--- 3. Checking Git Status of Deploy Repository ---")
    deploy_repo_root = os.path.abspath(os.path.join(deploy_dir, ".."))
    run_command("git status", cwd=deploy_repo_root)
    
    print("\n========================================================")
    print("SUCCESS: Web application built and PWA container verified!")
    print("To publish live, navigate to your deploy repo and run:")
    print("  git add .")
    print("  git commit -m \"deploy: update features and verify PWA container\"")
    print("  git push")
    print("========================================================\n")

if __name__ == "__main__":
    main()
