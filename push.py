import os, subprocess
cmds = [
    'git init',
    'git add .',
    'git commit -m "Update project structure and fix proxy"',
    'git branch -M main',
    'git remote add origin https://github.com/Mishakus/YandexGoogle-calendar-synchronization-tool.git',
    'git push -u origin main --force'
]
for c in cmds:
    print(f"Running: {c}")
    subprocess.run(c, shell=True, check=True)
