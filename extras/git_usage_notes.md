
# Git Usage Notes
## Preliminary
```bash
# Check you default branch name
git config --global --get init.defaultBranch		# expect main, not master

# Check other configuration parameters
git config --global --list --show-origin

# Set default branch to main
git config --global init.defaultBranch main
```

## Create the repo
```bash
# 1. Initialize the repo
git init

# 2. Stage everything
git add .

# 3. First commit
git commit -m "Initial commit"

# 4. Create the remote repo on GitHub and push
gh repo create jumpack-01 --public --source=. --remote=origin --push

```

## If the repo already exists on github
```bash
git remote add origin https://github.com/LouisB-CA/jumpack-01.git
git branch -M main
git push -u origin main
```


## If you get HEAD -> master instead of HEAD -> main
```bash
# Rename the local branch
git branch -m master main

# Push the new branch name and reset the upstream tracking
git push origin -u main

# Set the main branch to be default
gh api repos/LouisB-CA/jumpack-01 --method PATCH --field default_branch=main

# Delete the master branch
git push origin --delete master

```


## Updating the repo
```bash
# See what's modified
git status

# Stage all modified files
git add .

# Or stage specific files
git add <filename>

# Then commit
git commit -m "Update docs"

# Push
git push
```
