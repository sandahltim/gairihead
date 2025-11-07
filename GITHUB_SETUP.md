# GitHub Repository Setup - Final Steps

**Status**: Local repo ready, need to create remote on GitHub
**Commits**: 2 commits ready to push

---

## What's Done ✅

1. Git identity configured (`sandahltim <tim@broadwaytent.com>`)
2. Local repo initialized at `~/gairihead/`
3. Initial commit created (11,385 insertions, 40 files)
4. Migration guide added (second commit)
5. Gary README updated with GairiHead reference

---

## Next: Create GitHub Repository

### Step 1: Create Repo on GitHub

**Go to**: https://github.com/new

**Settings**:
- **Repository name**: `gairihead`
- **Description**: "GairiHead v2.0 - Expressive robot head with TARS personality"
- **Visibility**:
  - **Private** (recommended - contains your setup)
  - OR **Public** (if you want to share as open-source framework)
- **Initialize**: ❌ Do NOT check any boxes (we already have files)

Click **"Create repository"**

### Step 2: Copy Your Repository URL

GitHub will show you:
```
git remote add origin https://github.com/sandahltim/gairihead.git
```

**OR SSH** (if you have SSH keys configured):
```
git remote add origin git@github.com:sandahltim/gairihead.git
```

Copy this URL!

### Step 3: Push to GitHub

```bash
cd ~/gairihead

# Add remote (use URL from Step 2)
git remote add origin https://github.com/sandahltim/gairihead.git

# Push commits
git push -u origin main
```

**Done!** Your gairihead repo is now on GitHub.

---

## Verify Success

After pushing:

1. **Check GitHub**: Visit `https://github.com/sandahltim/gairihead`
   - Should see 40 files
   - README.md should display with badges
   - 2 commits in history

2. **Check local**:
   ```bash
   cd ~/gairihead
   git remote -v
   # Should show: origin  https://github.com/sandahltim/gairihead.git

   git status
   # Should show: Your branch is up to date with 'origin/main'
   ```

---

## Optional: Update Gary Repo

If you want to clean up the Gary repo:

```bash
cd /Gary

# Remove old GairiHead/ subdirectory
git rm -r GairiHead/

# Commit
git commit -m "refactor: Move GairiHead to separate repository

GairiHead now maintained at: https://github.com/sandahltim/gairihead
Integration unchanged (websocket protocol)"

# Push
git push
```

**Note**: This removes the old `/Gary/GairiHead/` folder. GairiHead is now only at `~/gairihead/`.

---

## Future Workflow

### Making Changes to GairiHead

```bash
cd ~/gairihead

# Make changes to files...

# Stage and commit
git add .
git commit -m "feat: Add new expression for skepticism"

# Push to GitHub
git push
```

### Deploying to Pi 5

```bash
cd ~/gairihead
./deploy.sh tim@100.103.67.41
```

**Independent!** No effect on Gary repo.

---

## Quick Reference

| Action | Command |
|--------|---------|
| Check status | `git status` |
| View commits | `git log --oneline` |
| See changes | `git diff` |
| Push changes | `git push` |
| Pull updates | `git pull` |

---

## Troubleshooting

### "Permission denied (publickey)"
Using SSH but no keys configured. Either:
1. Use HTTPS URL instead (will prompt for password)
2. Or setup SSH keys: https://docs.github.com/en/authentication/connecting-to-github-with-ssh

### "Remote origin already exists"
```bash
git remote remove origin
git remote add origin <your-url>
```

### "Failed to push"
```bash
# Make sure you're on main branch
git branch

# Try pulling first
git pull origin main --rebase
git push
```

---

## Summary

**Current state**:
```
~/gairihead/  ← Local repo with 2 commits, ready to push
/Gary/        ← Updated README references gairihead
```

**What you need to do**:
1. Create repo on GitHub (2 minutes)
2. Copy URL
3. Run `git remote add origin <url>` and `git push -u origin main`
4. Celebrate! 🎉

**Then optionally**:
- Clean up `/Gary/GairiHead/` folder
- Push Gary repo updates

---

**Status**: Ready for GitHub!
**Files staged**: 40 files, 11,385 lines
**Commits ready**: 2
**Next step**: Create GitHub repo
