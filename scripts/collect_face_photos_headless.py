#!/usr/bin/env python3
"""
Headless Face Photo Collection for GairiHead
Works over SSH without X11 display
Uses CameraManager for Pi Camera Module 3 support
"""

import sys
import cv2
import os
import time
from pathlib import Path
from datetime import datetime
import json

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from camera_manager import CameraManager

def collect_face_photos_headless(username, num_photos=20, output_dir=None, interval=2.0):
    """
    Collect face photos without display (headless mode for SSH)

    Args:
        username: Name of the person
        num_photos: Number of photos to collect
        output_dir: Output directory
        interval: Seconds between captures
    """
    if output_dir is None:
        script_dir = Path(__file__).parent.parent
        output_dir = script_dir / "data" / "known_faces" / username
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Load face detector
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )

    # Open camera using CameraManager (supports Pi Camera Module 3)
    try:
        cam = CameraManager(lazy_init=False)
        camera_info = cam.get_info()
        print(f"\n{'='*70}")
        print(f"📸 HEADLESS FACE PHOTO COLLECTION")
        print(f"{'='*70}")
        print(f"📷 Camera: {camera_info['type']} @ {camera_info['resolution']}")
    except Exception as e:
        print(f"❌ Error: Could not open camera: {e}")
        return False

    print(f"{'='*70}")
    print(f"👤 User: {username}")
    print(f"📁 Output: {output_dir}")
    print(f"🎯 Target: {num_photos} photos")
    print(f"⏱️  Interval: {interval}s between captures")
    print(f"{'='*70}\n")

    print("📋 INSTRUCTIONS:")
    print("  - Position yourself in front of the camera")
    print("  - Move your head through different angles:")
    print("    * Forward (straight at camera)")
    print("    * Left profile, right profile")
    print("    * Up (look down at camera)")
    print("    * Down (look up at camera)")
    print("  - Try different expressions (neutral, smile)")
    print("  - Auto-captures every 2 seconds when face detected")
    print(f"\n{'='*70}\n")

    # Check existing photos
    existing_photos = list(output_dir.glob(f"{username}_*.jpg"))
    if existing_photos:
        print(f"⚠️  Found {len(existing_photos)} existing photos")
        print("Continuing from existing count...")
        photos_captured = len(existing_photos)
    else:
        photos_captured = 0

    print("🎥 Camera ready! Starting capture in 3 seconds...")
    print("   Get into position...\n")
    time.sleep(3)

    last_capture_time = time.time()
    no_face_count = 0

    try:
        while photos_captured < num_photos:
            ret, frame = cam.read_frame()
            if not ret:
                print("❌ Error reading frame")
                break

            # Detect faces
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(100, 100)
            )

            current_time = time.time()

            if len(faces) > 0:
                no_face_count = 0

                # Check if enough time has passed
                if current_time - last_capture_time >= interval:
                    # Get largest face
                    largest_face = max(faces, key=lambda f: f[2] * f[3])
                    x, y, w, h = largest_face

                    # Calculate quality score
                    quality = w * h  # Face area
                    quality_pct = min(100, int((quality / (640 * 480)) * 100 * 10))

                    # Expand crop with padding
                    padding = int(w * 0.15)
                    x1 = max(0, x - padding)
                    y1 = max(0, y - padding)
                    x2 = min(frame.shape[1], x + w + padding)
                    y2 = min(frame.shape[0], y + h + padding)

                    face_crop = frame[y1:y2, x1:x2]

                    # Save photo
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
                    filename = output_dir / f"{username}_{timestamp}.jpg"
                    cv2.imwrite(str(filename), face_crop)

                    photos_captured += 1
                    last_capture_time = current_time

                    # Progress indicator with audio beep
                    progress_bar = "█" * photos_captured + "░" * (num_photos - photos_captured)
                    print(f"\a")  # System beep
                    print(f"📸✅ [{photos_captured:2d}/{num_photos}] {progress_bar} Quality: {quality_pct}% - {filename.name}")
                    print(f"   ⏱️  CAPTURED! Next photo in {interval} seconds...")

                    if photos_captured < num_photos:
                        # Provide guidance for next pose
                        if photos_captured % 4 == 0:
                            print("   💡 Try turning your head to the right →")
                        elif photos_captured % 4 == 1:
                            print("   💡 Try turning your head to the left ←")
                        elif photos_captured % 4 == 2:
                            print("   💡 Try looking up slightly ↑")
                        elif photos_captured % 4 == 3:
                            print("   💡 Try looking forward (neutral) →")
            else:
                no_face_count += 1
                if no_face_count > 10:  # ~1 second of no face
                    print("⚠️  No face detected - please position yourself in front of camera", end='\r')

            time.sleep(0.1)  # Small delay to reduce CPU usage

    except KeyboardInterrupt:
        print("\n\n⚠️  Capture interrupted (Ctrl+C)")

    finally:
        cam.close()

    print(f"\n{'='*70}")
    print(f"✅ COLLECTION COMPLETE")
    print(f"{'='*70}")
    print(f"📊 Photos captured: {photos_captured}")
    print(f"📁 Location: {output_dir}")
    print(f"{'='*70}\n")

    # Create metadata
    metadata = {
        "username": username,
        "authorization_level": 1,
        "photos_collected": photos_captured,
        "collection_date": datetime.now().isoformat(),
        "description": "Main authorized user",
        "collection_method": "headless_auto"
    }

    metadata_file = output_dir / "metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"💾 Metadata saved: {metadata_file}")

    return photos_captured > 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Headless face photo collection")
    parser.add_argument("username", help="Username (e.g., 'tim')")
    parser.add_argument("--num-photos", type=int, default=20, help="Number of photos")
    parser.add_argument("--interval", type=float, default=2.0, help="Seconds between captures")
    parser.add_argument("--output-dir", help="Output directory")

    args = parser.parse_args()

    success = collect_face_photos_headless(
        args.username,
        num_photos=args.num_photos,
        output_dir=args.output_dir,
        interval=args.interval
    )

    if success:
        print("\n🎉 SUCCESS! Next steps:")
        print("   1. Review photos in data/known_faces/tim/")
        print("   2. Generate encodings: python scripts/generate_face_encodings.py")
        print("   3. Test recognition: python scripts/test_face_recognition.py")
    else:
        print("\n❌ Collection failed - check camera connection")
