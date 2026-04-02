import os
import sys
import shutil
import subprocess
import argparse

def get_git_root():
    try:
        return subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], text=True).strip()
    except subprocess.CalledProcessError:
        return None

def install_local():
    git_root = get_git_root()
    if not git_root:
        print("❌ Error: Not a git repository. Cannot install locally.")
        return

    hooks_dir = os.path.join(git_root, '.git', 'hooks')
    target = os.path.join(hooks_dir, 'pre-commit')
    source = os.path.join(os.path.dirname(__file__), 'hooks', 'pre-commit')

    print(f"🔧 Installing local hook to {target}...")
    shutil.copy(source, target)
    print("✅ Local installation complete.")

def install_global():
    user_home = os.path.expanduser("~")
    global_hooks_dir = os.path.join(user_home, 'git-global-hooks')
    global_scanner_dir = os.path.join(user_home, 'gatekeeper')
    
    # 1. Create Directories
    os.makedirs(global_hooks_dir, exist_ok=True)
    os.makedirs(global_scanner_dir, exist_ok=True)

    # 2. Copy Scanner Logic
    current_src = os.path.dirname(os.path.abspath(__file__))
    print(f"📦 Migrating scanner logic to {global_scanner_dir}...")
    if os.path.exists(global_scanner_dir):
        shutil.rmtree(global_scanner_dir)
    shutil.copytree(current_src, global_scanner_dir)

    # 3. Create Global Hook Wrapper
    hook_target = os.path.join(global_hooks_dir, 'pre-commit')
    main_py_path = os.path.join(global_scanner_dir, 'hooks', 'main.py')
    
    # We use an absolute path to the global scanner's main.py
    hook_content = f"#!/bin/bash\npython \"{main_py_path}\"\n"
    
    with open(hook_target, 'w') as f:
        f.write(hook_content)

    print(f"🔧 Configuring Git global hooks path...")
    subprocess.run(['git', 'config', '--global', 'core.hooksPath', global_hooks_dir])
    
    print("✅ Global installation complete!")
    print(f"📌 Global Hooks: {global_hooks_dir}")
    print(f"📌 Global Scanner: {global_scanner_dir}")

def main():
    parser = argparse.ArgumentParser(description="Gatekeeper Security Hook Installer")
    parser.add_argument('--local', action='store_true', help="Install for the current repository only")
    parser.add_argument('--global', dest='is_global', action='store_true', help="Install globally for all repositories")

    args = parser.parse_args()

    if args.local:
        install_local()
    elif args.is_global:
        install_global()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
