"""
GairiHead NeoPixel Eye Controller
Runs on Raspberry Pi Pico - Controls 2x 12-pixel NeoPixel rings

Receives commands via UART from Pi 5, executes eye animations

Hardware:
- Pico GP2: Left eye ring (12 pixels)
- Pico GP3: Right eye ring (12 pixels)
- Pico GP0 (UART TX): Communication to Pi 5
- Pico GP1 (UART RX): Communication from Pi 5
"""

import board
import neopixel
import busio
import time
import math

# Pin definitions
LEFT_EYE_PIN = board.GP2
RIGHT_EYE_PIN = board.GP3
PIXEL_COUNT = 12

# Initialize UART (GP0=TX, GP1=RX)
uart = busio.UART(board.GP0, board.GP1, baudrate=115200, timeout=0.01)

# Initialize NeoPixel rings
left_eye = neopixel.NeoPixel(LEFT_EYE_PIN, PIXEL_COUNT, brightness=1.0, auto_write=False)
right_eye = neopixel.NeoPixel(RIGHT_EYE_PIN, PIXEL_COUNT, brightness=1.0, auto_write=False)

# Current state
current_expression = "idle"
current_color = (0, 100, 255)  # Blue
current_brightness = 128
animation_speed = 2000  # ms

# Animation state
animation_step = 0
last_update = time.monotonic()


def parse_command(cmd):
    """
    Parse incoming command from Pi 5

    Commands:
    - EXPR:idle - Set expression
    - COLOR:255,0,0 - Set RGB color
    - BRIGHTNESS:128 - Set brightness (0-255)
    - ANIM:blink - Trigger animation
    """
    cmd = cmd.strip()

    if cmd.startswith("EXPR:"):
        expression = cmd[5:].strip()
        set_expression(expression)
        return "OK"

    elif cmd.startswith("COLOR:"):
        try:
            rgb = cmd[6:].strip().split(',')
            r, g, b = int(rgb[0]), int(rgb[1]), int(rgb[2])
            set_color((r, g, b))
            return "OK"
        except:
            return "ERR:invalid_color"

    elif cmd.startswith("BRIGHTNESS:"):
        try:
            brightness = int(cmd[11:].strip())
            set_brightness(brightness)
            return "OK"
        except:
            return "ERR:invalid_brightness"

    elif cmd.startswith("ANIM:"):
        animation = cmd[5:].strip()
        trigger_animation(animation)
        return "OK"

    else:
        return "ERR:unknown_command"


def set_expression(expression):
    """Load expression preset"""
    global current_expression, current_color, current_brightness, animation_speed

    expressions = {
        'idle': {
            'color': (0, 100, 255),
            'brightness': 128,
            'animation': 'pulse',
            'speed': 2000
        },
        'listening': {
            'color': (0, 255, 255),
            'brightness': 200,
            'animation': 'solid',
            'speed': 0
        },
        'thinking': {
            'color': (0, 200, 255),
            'brightness': 180,
            'animation': 'chase',
            'speed': 1000
        },
        'alert': {
            'color': (255, 50, 0),
            'brightness': 255,
            'animation': 'flash',
            'speed': 500
        },
        'happy': {
            'color': (0, 255, 100),
            'brightness': 200,
            'animation': 'smile',
            'speed': 800
        },
        'sarcasm': {
            'color': (255, 180, 0),
            'brightness': 150,
            'animation': 'side_eye',
            'speed': 0
        }
    }

    if expression in expressions:
        expr = expressions[expression]
        current_expression = expression
        current_color = expr['color']
        current_brightness = expr['brightness']
        animation_speed = expr['speed']


def set_color(rgb):
    """Set solid color"""
    global current_color
    current_color = rgb
    for i in range(PIXEL_COUNT):
        left_eye[i] = rgb
        right_eye[i] = rgb
    left_eye.show()
    right_eye.show()


def set_brightness(brightness):
    """Set brightness (0-255)"""
    global current_brightness
    current_brightness = max(0, min(255, brightness))
    left_eye.brightness = current_brightness / 255.0
    right_eye.brightness = current_brightness / 255.0


def trigger_animation(animation):
    """Trigger one-shot animation"""
    if animation == "blink":
        animate_blink()


# ============================================================================
# ANIMATIONS
# ============================================================================

def animate_pulse():
    """Smooth brightness pulse"""
    global animation_step
    # Sine wave breathing effect
    brightness_factor = (math.sin(animation_step * 0.05) + 1) / 2  # 0.0 to 1.0
    brightness = int(current_brightness * brightness_factor)

    for i in range(PIXEL_COUNT):
        r = int(current_color[0] * brightness / 255)
        g = int(current_color[1] * brightness / 255)
        b = int(current_color[2] * brightness / 255)
        left_eye[i] = (r, g, b)
        right_eye[i] = (r, g, b)

    left_eye.show()
    right_eye.show()
    animation_step += 1


def animate_chase():
    """Rotating chase pattern"""
    global animation_step
    trail_length = 3

    # Clear all
    left_eye.fill((0, 0, 0))
    right_eye.fill((0, 0, 0))

    # Set trail
    for i in range(trail_length):
        pos = (animation_step + i) % PIXEL_COUNT
        brightness_factor = (trail_length - i) / trail_length
        r = int(current_color[0] * brightness_factor)
        g = int(current_color[1] * brightness_factor)
        b = int(current_color[2] * brightness_factor)
        left_eye[pos] = (r, g, b)
        right_eye[pos] = (r, g, b)

    left_eye.show()
    right_eye.show()
    animation_step = (animation_step + 1) % PIXEL_COUNT


def animate_flash():
    """Strobe effect"""
    global animation_step
    if animation_step % 2 == 0:
        left_eye.fill(current_color)
        right_eye.fill(current_color)
    else:
        left_eye.fill((0, 0, 0))
        right_eye.fill((0, 0, 0))

    left_eye.show()
    right_eye.show()
    animation_step += 1


def animate_smile():
    """Bottom pixels brighter (smile shape)"""
    # Pixels 3-9 are bottom arc (smile)
    for i in range(PIXEL_COUNT):
        if 3 <= i <= 9:
            left_eye[i] = current_color
            right_eye[i] = current_color
        else:
            r = int(current_color[0] * 0.4)
            g = int(current_color[1] * 0.4)
            b = int(current_color[2] * 0.4)
            left_eye[i] = (r, g, b)
            right_eye[i] = (r, g, b)

    left_eye.show()
    right_eye.show()


def animate_side_eye():
    """One ring dimmer (side-eye effect)"""
    left_eye.fill(current_color)
    # Right eye dimmer
    r = int(current_color[0] * 0.3)
    g = int(current_color[1] * 0.3)
    b = int(current_color[2] * 0.3)
    right_eye.fill((r, g, b))

    left_eye.show()
    right_eye.show()


def animate_blink():
    """Quick blink animation"""
    # Close
    left_eye.fill((0, 0, 0))
    right_eye.fill((0, 0, 0))
    left_eye.show()
    right_eye.show()
    time.sleep(0.1)

    # Open
    set_color(current_color)


def update_animation():
    """Main animation loop - call repeatedly"""
    global last_update

    now = time.monotonic()
    if animation_speed == 0:
        return  # No animation

    # Check if it's time to update
    interval = animation_speed / 1000.0  # Convert ms to seconds
    if now - last_update < interval / 30:  # 30 steps per cycle
        return

    last_update = now

    # Run appropriate animation
    if current_expression == "idle":
        animate_pulse()
    elif current_expression == "thinking":
        animate_chase()
    elif current_expression == "alert":
        animate_flash()
    elif current_expression == "happy":
        animate_smile()
    elif current_expression == "sarcasm":
        animate_side_eye()
    elif current_expression == "listening":
        # Solid - no animation
        set_color(current_color)


# ============================================================================
# MAIN LOOP
# ============================================================================

def main():
    """Main control loop"""
    print("GairiHead NeoPixel Controller v1.0")
    print("UART: 115200 baud on GP0/GP1")
    print("Eyes: GP2 (left), GP3 (right)")
    print("Ready for commands!")

    # Set initial state
    set_expression("idle")

    # Command buffer
    cmd_buffer = bytearray()

    while True:
        # Check for UART commands
        if uart.in_waiting > 0:
            data = uart.read(uart.in_waiting)
            if data:
                cmd_buffer.extend(data)

                # Process complete commands (newline-terminated)
                while b'\n' in cmd_buffer:
                    newline_idx = cmd_buffer.index(b'\n')
                    cmd_bytes = cmd_buffer[:newline_idx]
                    cmd_buffer = cmd_buffer[newline_idx+1:]

                    try:
                        cmd = cmd_bytes.decode('utf-8').strip()
                        if cmd:
                            print(f"RX: {cmd}")
                            response = parse_command(cmd)
                            uart.write(f"{response}\n".encode('utf-8'))
                            print(f"TX: {response}")
                    except Exception as e:
                        print(f"Error: {e}")
                        uart.write(b"ERR:parse_error\n")

        # Update current animation
        update_animation()

        # Small delay to prevent CPU thrashing
        time.sleep(0.001)


if __name__ == "__main__":
    main()
