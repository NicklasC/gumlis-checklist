import subprocess
import shutil
import os
import sys

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
    publish_cmd = (
        "flet publish src/main.py "
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
