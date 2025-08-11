"""
picarx_primitives.py

Primitive hardware control functions for SunFounder Picar-X robot.
Each function is self-contained and can be used in higher-level scripts or demos.
References:
- Your codebase (gpt_car.py, demo.py, etc.)
- Official SunFounder Picar-X examples: https://github.com/sunfounder/picar-x/tree/v2.0/example
"""

from picarx import Picarx
from robot_hat import Music
from robot_hat import Ultrasonic
import time
import os
from typing import List, Optional

# Singleton pattern for hardware objects
_picarx = None
def get_picarx() -> Picarx:
    global _picarx
    if _picarx is None:
        _picarx = Picarx()
    return _picarx

_music = None
def get_music() -> Music:
    global _music
    if _music is None:
        _music = Music()
    return _music

# Servo angle tracking
_servo_angles = {
    'dir_servo': 0,      # steering servo
    'cam_pan': 0,        # camera pan servo
    'cam_tilt': 0        # camera tilt servo
}

# --- Servo and Motor Primitives ---
def reset() -> None:
    """Reset all servos to 0 and stop the motors."""
    global _servo_angles
    px = get_picarx()
    px.set_dir_servo_angle(0)
    px.set_cam_pan_angle(0)
    px.set_cam_tilt_angle(0)
    px.stop()
    # Update tracked angles
    _servo_angles['dir_servo'] = 0
    _servo_angles['cam_pan'] = 0
    _servo_angles['cam_tilt'] = 0

def set_dir_servo(angle: float) -> None:
    """Set the direction (steering) servo angle (-30 to 30 typical)."""
    global _servo_angles
    px = get_picarx()
    px.set_dir_servo_angle(angle)
    _servo_angles['dir_servo'] = angle

def set_cam_pan_servo(angle: float) -> None:
    """Set the camera pan servo angle (-35 to 35 typical)."""
    global _servo_angles
    px = get_picarx()
    px.set_cam_pan_angle(angle)
    _servo_angles['cam_pan'] = angle

def set_cam_tilt_servo(angle: float) -> None:
    """Set the camera tilt servo angle (-35 to 35 typical)."""
    global _servo_angles
    px = get_picarx()
    px.set_cam_tilt_angle(angle)
    _servo_angles['cam_tilt'] = angle

def get_servo_angles() -> dict:
    """Get current angles of all servos."""
    global _servo_angles
    return _servo_angles.copy()

def get_dir_servo_angle() -> float:
    """Get current steering servo angle."""
    global _servo_angles
    return _servo_angles['dir_servo']

def get_cam_pan_angle() -> float:
    """Get current camera pan servo angle."""
    global _servo_angles
    return _servo_angles['cam_pan']

def get_cam_tilt_angle() -> float:
    """Get current camera tilt servo angle."""
    global _servo_angles
    return _servo_angles['cam_tilt']

def set_motor_speed(motor_id: int, speed: int) -> None:
    """
    Set the speed of an individual motor.
    motor_id: 1 (left), 2 (right)
    speed: -100 to 100
    """
    px = get_picarx()
    px.set_motor_speed(motor_id, speed)

# --- Motor Functions ---
def drive_forward(speed: int, duration: Optional[float] = None) -> None:
    """Drive forward at given speed (0-100). If duration is set, drive for that many seconds then stop."""
    px = get_picarx()
    px.forward(speed)
    if duration is not None:
        time.sleep(duration)
        px.stop()

def drive_backward(speed: int, duration: Optional[float] = None) -> None:
    """Drive backward at given speed (0-100). If duration is set, drive for that many seconds then stop."""
    px = get_picarx()
    px.backward(speed)
    if duration is not None:
        time.sleep(duration)
        px.stop()

def stop() -> None:
    """Stop all motors."""
    px = get_picarx()
    px.stop()

def turn_left(angle: float, speed: int = 30, duration: Optional[float] = None) -> None:
    """Turn left by setting steering angle and driving forward. Optionally for a duration."""
    px = get_picarx()
    px.set_dir_servo_angle(-abs(angle))
    px.forward(speed)
    if duration is not None:
        time.sleep(duration)
        px.stop()
        px.set_dir_servo_angle(0)

def turn_right(angle: float, speed: int = 30, duration: Optional[float] = None) -> None:
    """Turn right by setting steering angle and driving forward. Optionally for a duration."""
    global _servo_angles
    px = get_picarx()
    px.set_dir_servo_angle(abs(angle))
    _servo_angles['dir_servo'] = abs(angle)
    px.forward(speed)
    if duration is not None:
        time.sleep(duration)
        px.stop()
        px.set_dir_servo_angle(0)
        _servo_angles['dir_servo'] = 0

def scan_360_degrees(num_photos: int = 8) -> List[str]:
    """Scan 360 degrees while stationary, taking photos at each position."""
    global _servo_angles
    photo_filenames = []
    original_pan_angle = _servo_angles['cam_pan']
    
    # Calculate angles for 360 degree scan
    angles = []
    for i in range(num_photos):
        angle = -35 + (70 * i / (num_photos - 1))  # Spread across -35 to +35 degrees
        angles.append(angle)
    
    try:
        for i, angle in enumerate(angles):
            # Move camera to position
            set_cam_pan_servo(angle)
            time.sleep(0.5)  # Wait for servo to reach position
            
            # Take photo
            filename = f"scan_360_{i+1}_{int(angle)}_degrees.jpg"
            capture_image(filename)
            photo_filenames.append(filename)
            time.sleep(0.2)  # Brief pause between photos
        
        # Return camera to original position
        set_cam_pan_servo(original_pan_angle)
        
    except Exception as e:
        print(f"360 scan error: {e}")
        # Try to return camera to original position
        set_cam_pan_servo(original_pan_angle)
    
    return photo_filenames

def move_backward_safe(distance_cm: float = 20, speed: int = 30) -> bool:
    """Move backward safely for a specified distance."""
    px = get_picarx()
    
    # Calculate approximate duration based on distance and speed
    # This is rough - you may need to calibrate for your specific robot
    duration = distance_cm / (speed * 2)  # Rough approximation
    
    try:
        px.backward(speed)
        time.sleep(duration)
        px.stop()
        return True
    except Exception as e:
        print(f"Backward movement error: {e}")
        px.stop()
        return False

def rotate_in_place(degrees: float, speed: int = 30) -> bool:
    """Rotate the robot in place by the specified degrees. Positive = clockwise, Negative = counter-clockwise."""
    global _servo_angles
    px = get_picarx()
    
    try:
        # Set steering to maximum angle for tightest turn
        if degrees > 0:  # Clockwise rotation
            px.set_dir_servo_angle(30)  # Max right steering
            _servo_angles['dir_servo'] = 30
            # Use differential motor speeds for in-place rotation
            px.set_motor_speed(1, speed)   # Left motor forward
            px.set_motor_speed(2, -speed)  # Right motor backward
        else:  # Counter-clockwise rotation
            px.set_dir_servo_angle(-30)  # Max left steering
            _servo_angles['dir_servo'] = -30
            # Use differential motor speeds for in-place rotation
            px.set_motor_speed(1, -speed)  # Left motor backward
            px.set_motor_speed(2, speed)   # Right motor forward
        
        # Calculate rotation duration (this needs calibration for your specific robot)
        # Rough estimate: 90 degrees takes about 1 second at speed 30
        duration = abs(degrees) / 90.0 * 1.0 * (30.0 / speed)
        time.sleep(duration)
        
        # Stop and reset steering
        px.stop()
        px.set_dir_servo_angle(0)
        _servo_angles['dir_servo'] = 0
        
        return True
    except Exception as e:
        print(f"Rotation error: {e}")
        px.stop()
        px.set_dir_servo_angle(0)
        _servo_angles['dir_servo'] = 0
        return False

def turn_in_place_right(degrees: float = 45, speed: int = 30) -> bool:
    """Turn right in place by specified degrees (default 45°)."""
    return rotate_in_place(degrees, speed)

def turn_in_place_left(degrees: float = 45, speed: int = 30) -> bool:
    """Turn left in place by specified degrees (default 45°)."""
    return rotate_in_place(-degrees, speed)

def check_current_direction() -> dict:
    """Take a photo and check ultrasound in current direction to assess if it's an exit."""
    try:
        # Take photo in current direction
        filename = f"direction_check_{int(time.time())}.jpg"
        capture_image(filename)
        
        # Get distance reading
        distance = get_ultrasound()
        
        # Assess if this direction looks like an exit
        is_clear = distance > 30  # Consider clear if > 30cm
        is_exit_candidate = distance > 50  # Potential exit if > 50cm
        
        return {
            'photo_filename': filename,
            'distance_cm': distance,
            'is_clear': is_clear,
            'is_exit_candidate': is_exit_candidate,
            'assessment': 'EXIT CANDIDATE' if is_exit_candidate else 'CLEAR PATH' if is_clear else 'BLOCKED'
        }
    except Exception as e:
        print(f"Direction check error: {e}")
        return {
            'photo_filename': None,
            'distance_cm': 0,
            'is_clear': False,
            'is_exit_candidate': False,
            'assessment': 'ERROR',
            'error': str(e)
        }

def assess_environment() -> dict:
    """Take a photo and get sensor readings to assess current environment."""
    # Get distance reading
    distance = get_ultrasound()
    
    # Get current servo positions
    servo_angles = get_servo_angles()
    
    # Take assessment photo
    filename = f"assessment_{int(time.time())}.jpg"
    capture_image(filename)
    
    return {
        'distance_cm': distance,
        'servo_angles': servo_angles,
        'photo_filename': filename,
        'timestamp': time.time(),
        'too_close': distance < 15,  # Flag if too close to obstacle
        'safe_distance': distance > 30  # Flag if safe distance
    }

# --- Sensor Functions ---
def get_ultrasound() -> float:
    """Return distance in centimeters from the ultrasonic sensor."""
    px = get_picarx()
    return px.ultrasonic.read()

def get_grayscale() -> list:
    """Return list of grayscale sensor readings (0-4095, left to right)."""
    px = get_picarx()
    return px.get_grayscale_data()

# --- Camera Functions ---
_vilib_initialized = False

def init_camera() -> None:
    """Initialize the camera system. Call this once at startup."""
    global _vilib_initialized
    if not _vilib_initialized:
        try:
            from vilib import Vilib
            Vilib.camera_start(vflip=False, hflip=False)
            Vilib.display(local=False, web=True)
            
            # Wait for camera to be ready
            while True:
                if hasattr(Vilib, 'flask_start') and Vilib.flask_start:
                    break
                time.sleep(0.01)
            
            time.sleep(0.5)  # Additional stabilization time
            _vilib_initialized = True
            print("Camera initialized successfully")
        except Exception as e:
            print(f"Camera initialization error: {e}")

def capture_image(filename: str = "img_capture.jpg") -> None:
    """Capture an image from the camera and save to filename. Camera must be initialized first."""
    try:
        from vilib import Vilib
        import cv2
        
        # Initialize camera if not already done
        if not _vilib_initialized:
            init_camera()
        
        # Capture image using the same method as gpt_car.py
        if hasattr(Vilib, 'img') and Vilib.img is not None:
            cv2.imwrite(filename, Vilib.img)
            print(f"Image saved as {filename}")
        else:
            print("No image available from camera")
    except Exception as e:
        print(f"Camera capture error: {e}")

def take_photo_vilib(name: str = None, path: str = "./") -> str:
    """Take a photo using Vilib's built-in photo function."""
    try:
        from vilib import Vilib
        import time
        
        if not _vilib_initialized:
            init_camera()
        
        if name is None:
            from time import strftime, localtime
            name = f'photo_{strftime("%Y-%m-%d-%H-%M-%S", localtime(time.time()))}'
        
        Vilib.take_photo(name, path)
        full_path = f"{path}{name}.jpg"
        print(f'Photo saved as {full_path}')
        return full_path
    except Exception as e:
        print(f"Photo capture error: {e}")
        return ""

def close_camera() -> None:
    """Close the camera system. Call this when shutting down."""
    global _vilib_initialized
    if _vilib_initialized:
        try:
            from vilib import Vilib
            Vilib.camera_close()
            _vilib_initialized = False
            print("Camera closed")
        except Exception as e:
            print(f"Camera close error: {e}")

# --- Speaker Function ---
def play_sound(filename: str, volume: int = 100) -> None:
    """Play a sound file through the robot's speaker."""
    music = get_music()
    if os.path.isfile(filename):
        music.sound_play(filename, volume)
    else:
        print(f"Sound file not found: {filename}")

# --- Additional Primitives from Examples ---
def reset_servo(servo_id: int, angle: float = 0) -> None:
    """
    Set the specified servo to a given angle (default zero).
    servo_id: 0-11 (see hardware mapping)
    angle: angle to set (default 0)
    """
    from robot_hat import Servo
    Servo(servo_id).angle(angle)

def set_line_reference(refs: list) -> None:
    """Set grayscale line reference values (list of 3 ints)."""
    px = get_picarx()
    px.set_line_reference(refs)

def set_cliff_reference(refs: list) -> None:
    """Set grayscale cliff reference values (list of 3 ints)."""
    px = get_picarx()
    px.set_cliff_reference(refs)

def get_line_status(val_list: list) -> list:
    """Get line status from grayscale values (returns [bool, bool, bool])."""
    px = get_picarx()
    return px.get_line_status(val_list)

def get_cliff_status(val_list: list) -> bool:
    """Get cliff status from grayscale values (returns True if cliff detected)."""
    px = get_picarx()
    return px.get_cliff_status(val_list)

def camera_start(vflip: bool = False, hflip: bool = False) -> None:
    """Start the camera with optional vertical/horizontal flip."""
    from vilib import Vilib
    Vilib.camera_start(vflip=vflip, hflip=hflip)

def camera_display(local: bool = True, web: bool = True) -> None:
    """Display the camera feed locally and/or on the web."""
    from vilib import Vilib
    Vilib.display(local=local, web=web)

def color_detect(color: str) -> None:
    """Start color detection for the specified color (e.g., 'red', 'blue')."""
    from vilib import Vilib
    Vilib.color_detect(color)

def face_detect_switch(flag: bool) -> None:
    """Enable or disable face detection."""
    from vilib import Vilib
    Vilib.face_detect_switch(flag)

def qrcode_detect_switch(flag: bool) -> None:
    """Enable or disable QR code detection."""
    from vilib import Vilib
    Vilib.qrcode_detect_switch(flag)

def take_photo(name: str, path: str) -> None:
    """Take a photo and save it to the specified path with the given name."""
    from vilib import Vilib
    Vilib.take_photo(name, path)

# --- Example Usage ---
if __name__ == "__main__":
    print("Testing Picar-X primitives...")
    set_dir_servo(0)
    set_cam_pan_servo(0)
    set_cam_tilt_servo(0)
    drive_forward(30, 1)
    turn_left(20, 30, 0.5)
    drive_backward(30, 1)
    stop()
    print(f"Ultrasound: {get_ultrasound():.1f} cm")
    print(f"Grayscale: {get_grayscale()}")
    capture_image("test.jpg")
    # play_sound("../sounds/car-double-horn.wav") 