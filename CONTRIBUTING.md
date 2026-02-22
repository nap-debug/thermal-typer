## Working locally (Pi off)

1. Open Git Bash
2. `cd ~/thermal-typer && code .`
3. Write code, save files
4. `git add .` → `git commit -m "..."` → `git push`

Or:

1. Open VSCode
2. choose thermal-typer from recent projects. 

On the Home PC, thermal-typer lives in:
C:\Users\Eduardo\Documents\Projects\thermal-typer-vscode

## Deploying to the Pi

1. SSH into Pi: `ssh printerpi`
2. `cd ~/thermal-typer`
3. `git pull`
4. `sudo systemctl restart typewriter`