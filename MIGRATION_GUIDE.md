# GairiHead Repository Migration Guide

**Date**: 2025-11-07
**Status**: Ready to migrate
**Time required**: ~10 minutes

---

## Overview

GairiHead is now a separate repository from the main Gary system.

**Benefits**:
- Independent deployment to Pi 5
- Clean git history (hardware vs business logic)
- Rapid hardware iteration without affecting Gary
- Could be open-sourced as standalone framework
- Simpler CI/CD for Pi 5 deployment

---

## Current State

### ✅ Complete
- New repo created at `~/gairihead/`
- All files copied from `/Gary/GairiHead/`
- `.gitignore` configured
- README updated for standalone repo
- Git repo initialized (on `main` branch)

### ⏳ Needs Configuration
- Git user identity (see Step 1)
- Remote repository URL (GitHub/GitLab)
- Gary repo update (remove GairiHead/, update docs)

---

## Migration Steps

### Step 1: Configure Git Identity

```bash
cd ~/gairihead

# Option A: Set globally (all repos)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Option B: Set for this repo only
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

### Step 2: Create Initial Commit

```bash
cd ~/gairihead
git add .
git commit -m "feat: Initial commit - GairiHead v2.0 with personality

- 24 expressive states (idle, sarcasm, deadpan, celebration, etc.)
- Smooth servo movement with easing curves
- Contextual memory & mood drift
- Personality quirks (winks after sarcasm, sighs, micro-expressions)
- Websocket API for remote control
- Camera & face detection
- Two-tier LLM intelligence (local + cloud)
- Complete documentation (650+ line expression guide)

Hardware: Pi 5, Pico 2, 3x servos, 2x NeoPixel rings, camera
Status: Software complete, awaiting servo hardware for testing

TARS-like personality: Dry wit, competent, subtly caring"
```

### Step 3: Create Remote Repository

**On GitHub/GitLab**:
1. Go to github.com (or your git provider)
2. Create new repository named `gairihead`
3. Don't initialize with README (we already have one)
4. Copy the repository URL

**Example URLs**:
- SSH: `git@github.com:yourusername/gairihead.git`
- HTTPS: `https://github.com/yourusername/gairihead.git`

### Step 4: Link and Push

```bash
cd ~/gairihead

# Add remote
git remote add origin <your-repo-url>

# Push to remote
git push -u origin main
```

### Step 5: Update Gary Repository

**Remove GairiHead subdirectory** (it's now separate):

```bash
cd /Gary

# Remove GairiHead/ folder from Gary repo
git rm -r GairiHead/

# Commit the change
git commit -m "refactor: Move GairiHead to separate repository

GairiHead is now maintained independently at:
https://github.com/yourusername/gairihead

Integration remains via websocket (ws://100.103.67.41:8766)

Changed:
- Removed /Gary/GairiHead/ subdirectory
- Updated README with link to gairihead repo
- No changes to src/tools/gairi_head_tool.py (websocket client)"

# Push
git push
```

### Step 6: Update Gary README

Add to `/Gary/README.md`:

```markdown
## Physical Robot Integration

GairiHead (physical robot head) is maintained as a separate project.

**Repository**: https://github.com/yourusername/gairihead
**Integration**: Websocket API (`ws://100.103.67.41:8766`)
**Tool**: `src/tools/gairi_head_tool.py` (client library)

Commands available:
- `capture_snapshot()` - Camera photo
- `detect_faces()` - Face detection
- `record_audio()` - Microphone recording
- `set_expression()` - Change facial expression
- `analyze_scene()` - Photo + face detection

See gairihead repo for hardware setup and documentation.
```

---

## Deployment Workflow

### Before (Single Repo)
```bash
cd /Gary/GairiHead
rsync ... tim@100.103.67.41:~/GairiHead/
# Had to sync entire /Gary repo changes
```

### After (Separate Repos)

**GairiHead changes** (Pi 5):
```bash
cd ~/gairihead
./deploy.sh tim@100.103.67.41
# Or: git push (if auto-deploy configured)
```

**Gary changes** (Server):
```bash
cd /Gary
git push
# Deploy to server (unchanged)
```

**Independent, clean, fast!**

---

## File Locations

### GairiHead Repo (`~/gairihead/`)
```
gairihead/
├── src/
│   ├── gairi_head_server.py       # Websocket server
│   ├── expression_engine.py
│   ├── servo_controller.py
│   └── ...
├── config/
├── docs/
├── tests/
├── README.md
└── .git/
```

### Gary Repo (`/Gary/`)
```
gary/
├── src/
│   ├── tools/
│   │   └── gairi_head_tool.py    # ← Client stays here
│   └── ...
├── data/
├── README.md  # ← Add link to gairihead
└── .git/
```

**Connection**: Websocket protocol, network-separated

---

## Testing After Migration

### 1. Test GairiHead Repo
```bash
cd ~/gairihead
git status  # Should be clean
git remote -v  # Should show origin
git log  # Should show initial commit
```

### 2. Test Deployment
```bash
cd ~/gairihead
./deploy.sh tim@100.103.67.41
# Should sync files to Pi 5
```

### 3. Test Gary Integration
```bash
cd /Gary
python -c "from src.tools.gairi_head_tool import GairiHeadTool; print('✅ Tool imports')"
# Should work (client doesn't care where server code lives)
```

### 4. Test Websocket Connection
```bash
# On Pi 5
cd ~/gairihead
source venv/bin/activate
python src/gairi_head_server.py

# On server (different terminal)
cd /Gary
source venv/bin/activate
python -c "from src.tools.gairi_head_tool import test_gairi_head_connection; test_gairi_head_connection()"
# Should connect and work
```

---

## Rollback Plan

If something goes wrong:

### Restore GairiHead to Gary repo
```bash
# 1. Copy files back
cp -r ~/gairihead /Gary/GairiHead

# 2. Git add back in Gary repo
cd /Gary
git add GairiHead/
git commit -m "Restore GairiHead to main repo"

# 3. Remove separate repo
rm -rf ~/gairihead
```

**Note**: Not recommended unless integration breaks (which it shouldn't - websocket is network-separated)

---

## Future Enhancements

### Auto-Deploy on Push
Set up GitHub Actions in gairihead repo:

```yaml
# .github/workflows/deploy.yml
name: Deploy to Pi 5
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy
        run: |
          ./deploy.sh ${{ secrets.PI5_HOST }}
```

### Submodule (Optional)
If you want GairiHead accessible from Gary repo:

```bash
cd /Gary
git submodule add https://github.com/yourusername/gairihead GairiHead
```

**Not recommended** - they're separate systems

---

## Checklist

- [ ] Configure git identity (`git config user.name/email`)
- [ ] Create initial commit in gairihead repo
- [ ] Create remote repository (GitHub/GitLab)
- [ ] Link remote and push (`git remote add origin ...`)
- [ ] Remove `/Gary/GairiHead/` from Gary repo
- [ ] Update Gary README with link
- [ ] Test deployment to Pi 5
- [ ] Test websocket connection
- [ ] Celebrate clean separation! 🎉

---

## Support

**Issues with gairihead**: Create issue in gairihead repo
**Issues with Gary integration**: Check `src/tools/gairi_head_tool.py` in Gary repo
**Websocket connection issues**: Verify Pi 5 accessible at `100.103.67.41:8766`

---

## Summary

**What changed**:
- GairiHead is now separate repo
- Gary repo no longer contains `/Gary/GairiHead/`
- Integration unchanged (websocket protocol)

**What didn't change**:
- Websocket API (same endpoints)
- `gairi_head_tool.py` location (stays in Gary)
- Pi 5 deployment location (`~/gairihead/`)
- How you use GairiHead from Gary

**Benefits**:
- ✅ Independent version control
- ✅ Clean git history
- ✅ Rapid hardware iteration
- ✅ Independent deployment
- ✅ Could be open-sourced
- ✅ Clearer project boundaries

---

**Migration Status**: Ready to execute
**Risk**: LOW (network-separated systems)
**Time**: ~10 minutes
**Reversible**: YES (see Rollback Plan)

Ready when you are!
