# 3D Print Files for GairiHead

## Bubo-2T Template

**Source**: https://www.kevsrobots.com/blog/bubo-2t.html

**STL Files Listed** (14 files):
- face.stl
- back.stl
- body.stl
- bottom.stl
- base.stl
- eye_piece.stl
- Various arm and eyelid components

**Status**: Files mentioned on website but not in GitHub repo
**Next**: Visit website directly and check for download links

**GitHub Code**: https://github.com/kevinmcaleer/bubo-2t
- Contains Python scripts (hand.py, face.py, toot.py)
- No STL files in repo

---

## Alternative Sources

### Option 1: Custom Design
- Design simple head shell in Fusion 360 or Blender
- Servo mounts for SG90 servos
- NeoPixel ring mounts (12-pixel)
- Camera module mount (Pi Camera 3)

### Option 2: Generic Robot Head
Search Thingiverse/Printables for:
- "robot head raspberry pi"
- "animatronic eyes servos"
- "neopixel eye rings"

### Option 3: Contact Creator
- Reach out to Kevin McAleer (kevsrobots.com)
- STL files might be available on request
- May be paywalled or in a separate download

---

## Required Components to House

### Servos (3x SG90)
- Left eyelid: 9mm x 23mm x 25mm
- Right eyelid: 9mm x 23mm x 25mm
- Mouth: 9mm x 23mm x 25mm

### NeoPixel Rings (2x)
- Outer diameter: ~45mm
- Inner diameter: ~30mm
- Height: ~5mm

### Pi Camera Module 3
- PCB: 25mm x 24mm
- Lens height: ~10mm
- Needs CSI ribbon cable access

### Pi 5
- Board: 56mm x 85mm
- Height with HAT: ~50mm
- Needs ventilation

### Pico W
- Board: 21mm x 51mm
- Height: ~5mm
- USB connection for programming

### USB Mic + Speaker
- Mic: ~50mm diameter (typical)
- Speaker: ~60mm diameter (typical)
- Need acoustic ports in head

---

## Design Considerations

### Head Size
- Internal volume: ~150mm x 150mm x 200mm (estimate)
- Eye spacing: ~80-100mm apart
- Needs cable routing space

### Servo Mounting
- Eyelid servos: Behind/above eyes
- Mouth servo: Below eyes
- Need rigid mounting (no flex)

### Power/Cables
- Servo power supply inside or external
- Cable routing to servos
- USB cables for mic/speaker
- CSI ribbon to camera

### Ventilation
- Pi 5 generates heat (~5W)
- Need air vents top/bottom
- Consider small 40mm fan

### Assembly
- Snap-fit or screws
- Access panels for maintenance
- Cable management clips
- Removable back panel

---

## Next Steps

1. **Visit Bubo-2T website directly** and look for download button
2. **Check Thingiverse/Printables** for similar designs
3. **Consider custom design** if no suitable templates found
4. **Test fit components** before final print (use cardboard mockup)

---

**Status**: Research in progress
**Priority**: MEDIUM - Can use cardboard/temp mount for initial servo testing
**Timeline**: Need before final assembly (Phase 8)
