# GairiHead Sound Effects

This directory contains sound effect files for stage direction markers.

## Required Sound Files

Place `.wav` or `.mp3` files here with these names:

### High Priority (Common Markers)
- `sigh.wav` - For *sighs*
- `chuckle.wav` - For *chuckle* / *chuckles*
- `laugh.wav` - For *laughs* / *laughing*
- `breath.wav` - For *takes a breath*

### Medium Priority
- `gasp.wav` - For *gasps*
- `groan.wav` - For *groans*
- `yawn.wav` - For *yawns*
- `snicker.wav` - For *snicker* / *snickers*

### Optional (Creative)
- `chair_squeak.wav` - For "leans back" / chair movements
- `gulp.wav` - For nervous/dramatic moments
- `hmm.wav` - For thoughtful moments

## Format Requirements

- **Format**: WAV (preferred) or MP3
- **Sample Rate**: 16kHz or 44.1kHz (will be auto-converted)
- **Channels**: Mono preferred (stereo will be converted)
- **Duration**: Keep short (0.5-2 seconds)
- **Volume**: Will be normalized automatically

## Finding Sound Effects

**Free Resources**:
- [Freesound.org](https://freesound.org) - CC0/CC-BY sounds
- [Zapsplat.com](https://zapsplat.com) - Free sound effects
- [BBC Sound Effects](http://bbcsfx.acropolis.org.uk/) - Public domain

**Search Terms**:
- "human sigh", "man sigh"
- "chuckle", "short laugh"
- "gasp", "surprised gasp"
- "deep breath", "exhale"
- "chair squeak", "office chair"

## Testing

Test sound effects:
```bash
python -m src.stage_actions
```

## Current Status

- ✅ Sound system implemented
- ⏳ Waiting for sound effect files
- 📁 Place .wav/.mp3 files in this directory
- 🔄 Files loaded automatically on startup

**Note**: GairiHead will work without sound files (just won't play effects).
