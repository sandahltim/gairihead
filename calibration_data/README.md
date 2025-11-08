# Servo Calibration Data

This directory contains the physical calibration data for all MG90S analog servos.

## Calibration Files

### Left Eye (GPIO 17)
- File: `left_eye_calibration.txt`
- Range: 0-75° (physical mechanism limit)
- Servo values: 0.100 (closed) → -0.310 (open)
- Working span: 0.410

### Right Eye (GPIO 27)
- File: `right_eye_calibration.txt`
- Range: 0-75° (physical mechanism limit)
- Servo values: -0.100 (closed) → 0.310 (open)
- Working span: 0.410 (inverted from left eye for symmetry)

### Mouth (GPIO 22)
- File: `mouth_calibration.txt`
- Range: 0-60° (physical mechanism limit)
- Servo values: 0.000 (closed) → -0.600 (open)
- Working span: 0.600

## Notes

- All servos are MG90S analog servos (metal gear, 9g micro)
- Calibration performed: 2025-11-08
- Digital servos will be installed later for improved precision and reduced twitching
- These calibrations are hardcoded into `src/servo_controller.py`

## Recalibration

If servos need recalibration:
1. Use `scripts/precise_servo_calibration.py` (generic tool)
2. Or use specific tools: `scripts/calibrate_mouth.py`
3. Update the corresponding function in `src/servo_controller.py`
4. Update this README with new values
