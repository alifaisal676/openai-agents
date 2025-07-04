# Git Commands Reference for Triage Project

## Daily Workflow Commands

### Check Status
```bash
git status                    # See what files have changed
git diff                     # See exact changes in files
git log --oneline           # See recent commits
```

### Making Updates
```bash
git add .                    # Add all changed files
git add filename.py         # Add specific file
git commit -m "Your message" # Commit with description
git push origin main        # Upload to GitHub
```

### Getting Latest Changes
```bash
git pull origin main        # Download latest from GitHub
```

## Common Update Scenarios

### Adding New Features
```bash
git add new_feature.py classifier.py
git commit -m "Add support for insurance forms"
git push origin main
```

### Bug Fixes
```bash
git add api.py
git commit -m "Fix: Handle network timeout errors"
git push origin main
```

### Documentation Updates
```bash
git add README.md
git commit -m "Update installation guide with troubleshooting"
git push origin main
```

### Environment Updates
```bash
git add requirements.txt .gitignore
git commit -m "Add new dependencies and ignore patterns"
git push origin main
```

## Branch Management (Advanced)

### Create Feature Branch
```bash
git checkout -b feature/new-document-type
# Make changes
git add .
git commit -m "Implement insurance form processing"
git push origin feature/new-document-type
# Create Pull Request on GitHub
```

### Switch Branches
```bash
git checkout main           # Switch to main branch
git checkout feature-name   # Switch to feature branch
```

## Useful Tips

1. **Always check status before committing:**
   ```bash
   git status
   ```

2. **See what changed in a file:**
   ```bash
   git diff filename.py
   ```

3. **Undo last commit (if not pushed yet):**
   ```bash
   git reset --soft HEAD~1
   ```

4. **View commit history:**
   ```bash
   git log --oneline --graph
   ```

5. **Check remote repository:**
   ```bash
   git remote -v
   ```

## Emergency Commands

### Discard Changes to a File
```bash
git checkout -- filename.py
```

### Discard All Local Changes
```bash
git reset --hard HEAD
```

### Force Pull (Overwrite Local Changes)
```bash
git fetch origin
git reset --hard origin/main
```

## Best Practices

- ✅ Commit often with clear messages
- ✅ Pull before starting work
- ✅ Test your code before committing
- ✅ Use descriptive commit messages
- ✅ Keep commits focused (one feature/fix per commit)
- ❌ Don't commit broken code
- ❌ Don't use vague commit messages
- ❌ Don't commit sensitive information (API keys, passwords)
