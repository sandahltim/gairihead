# GairiHead Camera Setup

**USB Camera and Pi Camera Module support with automatic detection**

---

## Quick Start

### Test Your Camera

```bash
ssh tim@100.103.67.41
cd ~/GairiHead
source venv/bin/activate
python tests/test_camera.py
```

**Choose option**:
1. Basic test - Capture 30 frames, verify camera working
2. Face detection - Live face tracking (look at camera!)
3. Both tests

---

## Supported Cameras

### ✅ USB Cameras (Available Now)
- **Any USB webcam** (Logitech, generic, etc.)
- Works via OpenCV (cv2.VideoCapture)
- Plug-and-play on Linux
- Perfect for development and testing
- **Detected at**: `/dev/video0` (or video1, video2...)

### ✅ Pi Camera Module 3 (When it arrives)
- Better image quality
- Lower CPU usage (hardware encoding)
- CSI connector (no USB needed)
- Auto-detected via `picamera2`
- **Requires**: `sudo apt install python3-picamera2`

---

## How Camera Manager Works

**Automatic Detection:**
```python
from camera_manager import CameraManager

# Tries USB first, falls back to Pi Camera
with CameraManager() as cam:
    ret, frame = cam.read_frame()
    # frame is numpy array, ready for OpenCV/CV2
```

**Manual preference:**
```python
# Prefer Pi Camera, fall back to USB
cam = CameraManager(prefer_picam=True)

# Prefer USB (default)
cam = CameraManager(prefer_picam=False)
```

**Always returns BGR format** - Works identically with OpenCV functions regardless of camera type!

---

## USB Camera Setup

### 1. Check If Detected

```bash
# List video devices
ls -l /dev/video*

# Expected output:
# crw-rw----+ 1 root video 81, 0 Nov  6 10:00 /dev/video0
```

### 2. Test with v4l2

```bash
# Install v4l-utils if not present
sudo apt install v4l-utils

# Check camera info
v4l2-ctl --device=/dev/video0 --all

# List supported formats
v4l2-ctl --device=/dev/video0 --list-formats-ext
```

### 3. Test with GairiHead

```bash
cd ~/GairiHead
source venv/bin/activate
python tests/test_camera.py
```

Should see window with camera feed!

---

## Pi Camera Module 3 Setup

### 1. Install picamera2

```bash
sudo apt update
sudo apt install -y python3-picamera2
```

### 2. Enable Camera Interface

```bash
sudo raspi-config
# Navigate to: Interface Options -> Camera -> Enable
```

### 3. Check Detection

```bash
# Check if camera detected
vcgencmd get_camera

# Expected: detected=1, supported=1
```

### 4. Test with GairiHead

```bash
cd ~/GairiHead
source venv/bin/activate
python tests/test_camera.py
```

CameraManager will automatically use Pi Camera if detected!

---

## Configuration

Edit `/Gary/GairiHead/config/gairi_head.yaml`:

```yaml
hardware:
  pi5:
    camera_device: 0        # USB device ID (0=/dev/video0)
    camera_resolution: [640, 480]
    camera_fps: 5           # Lower for local LLM vision
```

**Resolution options:**
- 640x480 - Fast, good for face detection
- 1280x720 - Higher quality
- 1920x1080 - Best quality (slower)

**FPS recommendations:**
- 5fps - Good for ambient monitoring
- 15fps - Smooth face tracking
- 30fps - Recording quality

---

## Vision Features (Future)

### Face Detection (OpenCV)
```python
from camera_manager import CameraManager
import cv2

with CameraManager() as cam:
    ret, frame = cam.read_frame()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )
    faces = cascade.detectMultiScale(gray, 1.1, 5)
```

### Face Recognition
- Use `face_recognition` library
- Store Tim's face in `/Gary/GairiHead/data/faces/tim/`
- Distinguish Tim from strangers

### Eye Tracking
- Track face position in frame
- Move servos to follow Tim around room
- "Look at person" behavior

### Llama Vision (Local LLM)
```python
# Send frame to Llama 3.2 Vision
response = llm.analyze_frame(frame, prompt="Is Tim frustrated?")
```

---

## Troubleshooting

### USB Camera Not Found

**Problem**: No `/dev/video0`

**Solutions**:
```bash
# Check USB devices
lsusb | grep -i camera

# Check dmesg for errors
dmesg | grep -i video

# Try different USB port
# Some Pi USB ports have better power
```

### Permission Denied

**Problem**: Can't access `/dev/video0`

**Solution**:
```bash
# Add user to video group
sudo usermod -a -G video $USER

# Logout and back in for group change
```

### Camera Opens But No Image

**Problem**: `read_frame()` returns False

**Solutions**:
```bash
# Check if other program using camera
lsof /dev/video0

# Kill if found
sudo pkill -f <program_name>

# Try different resolution in config
```

### Pi Camera Module Not Detected

**Problem**: `vcgencmd get_camera` shows `detected=0`

**Solutions**:
```bash
# Check cable connection (CSI connector)
# Power off before reconnecting!

# Enable camera interface
sudo raspi-config
# Interface Options -> Camera -> Enable

# Reboot
sudo reboot
```

### Window Not Showing (Headless)

**Problem**: SSH session, no display

**Solution**:
```bash
# Enable X11 forwarding
ssh -X tim@100.103.67.41

# Or save frames instead
# Modify test to use cv2.imwrite() instead of imshow()
```

---

## Performance Tips

### Reduce CPU Usage
- Lower FPS in config (5fps for ambient)
- Lower resolution (640x480 is plenty)
- Use Pi Camera Module (hardware encoding)

### Faster Face Detection
```python
# Resize frame before processing
small_frame = cv2.resize(frame, (320, 240))
faces = cascade.detectMultiScale(small_frame, ...)
```

### Battery/Power Saving
- Set `camera_fps_idle: 1` in config
- Reduce resolution when no face detected
- Turn off camera when no motion

---

## Integration with GairiHead

### Expression Sync
```python
# When face detected -> alert expression
if len(faces) > 0:
    servo_controller.set_expression('alert')
```

### Eye Tracking
```python
# Move eyes to follow face
face_x = (x + w/2) / frame_width  # 0-1
eye_angle = face_x * 90  # Map to servo range
```

### Proactive Behavior
```python
# Check for Tim's arrival
if face_recognized == "Tim":
    speak("Morning. How's the chaos today?")
    set_expression('happy')
```

---

## Next Steps

1. **Now**: Test USB camera with `test_camera.py`
2. **Next**: Add face detection to main loop
3. **Later**: Face recognition (Tim vs strangers)
4. **Future**: Eye tracking servo control

---

## Files

**Source**: `/Gary/GairiHead/src/camera_manager.py`
**Tests**: `/Gary/GairiHead/tests/test_camera.py`
**Config**: `/Gary/GairiHead/config/gairi_head.yaml`

---

**Updated**: 2025-11-06
**Status**: USB camera ready to test, Pi Camera support ready
