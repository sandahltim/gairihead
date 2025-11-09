# Running GairiHead

## Quick Start

GairiHead requires **two processes** to run for full functionality:

1. **Main App** - Voice assistant (port 8765 → Gary)
2. **Server** - Remote control for Gary (port 8766 ← Gary)

### One-Command Startup

```bash
cd /home/tim/GairiHead
./scripts/start_gairihead.sh
```

This starts both processes in the background.

### Management Commands

```bash
# Check status
./scripts/status_gairihead.sh

# View logs in real-time
tail -f logs/gairihead_main.log
tail -f logs/gairihead_server.log

# Restart (stop then start)
./scripts/restart_gairihead.sh

# Stop
./scripts/stop_gairihead.sh
```

---

## Architecture

### Main App (`main.py`)
**What it does:**
- Waits for touchscreen button press
- Scans face for authorization
- Records voice query (VAD auto-stop)
- Sends to Gary server (port 8765)
- Speaks Gary's response
- Animates mouth during speech
- Updates Arduino display

**Modes:**
- `--mode production` - Touchscreen button trigger (default)
- `--mode interactive` - Keyboard Enter trigger
- `--mode continuous` - Auto-trigger every N seconds
- `--mode test` - Component tests only

### Server (`src/gairi_head_server.py`)
**What it does:**
- WebSocket server on port 8766
- Allows Gary to control GairiHead remotely

**Commands Gary can send:**
- `capture_snapshot` - Get camera image
- `record_audio` - Record N seconds of audio
- `analyze_scene` - Camera + face detection
- `detect_faces` - Fast face detection
- `get_status` - System status
- `set_expression` - Change facial expression

---

## Manual Startup (Development)

If you need to run components separately:

**Terminal 1 - Server:**
```bash
cd /home/tim/GairiHead
source venv/bin/activate
python3 src/gairi_head_server.py
```

**Terminal 2 - Main App:**
```bash
cd /home/tim/GairiHead
source venv/bin/activate
python3 main.py --mode production
```

---

## Running on Boot (systemd)

To start GairiHead automatically on Pi boot:

1. Create systemd service:
```bash
sudo nano /etc/systemd/system/gairihead.service
```

2. Add:
```ini
[Unit]
Description=GairiHead Voice Assistant
After=network.target

[Service]
Type=forking
User=tim
WorkingDirectory=/home/tim/GairiHead
ExecStart=/home/tim/GairiHead/scripts/start_gairihead.sh
ExecStop=/home/tim/GairiHead/scripts/stop_gairihead.sh
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

3. Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable gairihead
sudo systemctl start gairihead
```

4. Check status:
```bash
sudo systemctl status gairihead
```

---

## Troubleshooting

### Check if running
```bash
./scripts/status_gairihead.sh
```

### View recent logs
```bash
# Last 50 lines
tail -50 logs/gairihead_main.log
tail -50 logs/gairihead_server.log

# Follow in real-time
tail -f logs/gairihead_main.log
```

### Common Issues

**Arduino not detected:**
- Check USB connection: `ls /dev/ttyACM*`
- Check permissions: `sudo usermod -a -G dialout tim`
- Reconnect Arduino USB

**Camera not working:**
- Check device: `ls /dev/video*`
- Try device 0 or 1 in config
- Check permissions: `sudo usermod -a -G video tim`

**Servos not moving:**
- Check GPIO permissions (need to run as user with GPIO access)
- Verify pin configuration in `config/gairi_head.yaml`
- Test manually: `python3 scripts/test_servos.py`

**Gary connection fails:**
- Verify Gary server is running on 100.106.44.11:8765
- Check Tailscale connection: `tailscale status`
- Test with: `curl -v http://100.106.44.11:8765`

**Face recognition not working:**
- Run diagnostic: `python3 scripts/test_face_debug.py`
- Check training photos: `ls data/known_faces/tim/`
- Adjust detection params in config if needed

---

## Configuration

Main config: `config/gairi_head.yaml`

Key settings:
- `intelligence.gary_websocket_url` - Gary server address
- `hardware.arduino_display.port` - Arduino USB port
- `hardware.servos.*` - Servo GPIO pins and calibration
- `voice.microphone.device_index` - USB mic device
- `vision.face_detection.*` - Face detection sensitivity

---

## Logs

Logs are stored in: `logs/`

- `gairihead_main.log` - Main app logs
- `gairihead_server.log` - Server logs
- `gairi_head_YYYY-MM-DD.log` - Daily rotating logs

Logs rotate daily and keep 30 days of history.

---

## Performance

Typical resource usage:
- **Main App**: ~200-300 MB RAM, 10-20% CPU (idle)
- **Server**: ~100-150 MB RAM, <5% CPU (idle)

During voice interaction:
- CPU spikes to 50-80% (VAD, transcription, TTS)
- Returns to idle after response
