"""
This is Rachits attempt to code the final primitives for the picarx robot.
"""

from picarx import Picarx
import time
from typing import List, Optional
from robot_hat import Ultrasonic
import os
from robot_hat import Music

#global variable for the picarx object
_picarx = None

#function to get the picarx object
def get_picarx() -> Picarx:
    global _picarx # call the global variable since we are assigning it a value
    if _picarx is None:
        _picarx = Picarx()
    return _picarx

#dictionary to store the servo angles
_servo_angles = {
    'dir_servo': 0,
    'cam_pan': 0,
    'cam_tilt': 0
}

def reset() -> None:
    global _servo_angles
    px = get_picarx()
    px.set_dir_servo_angle(0)
    px.set_cam_pan_angle(0)
    px.set_cam_tilt_angle(0)
    px.stop()
    _servo_angles['dir_servo'] = 0
    _servo_angles['cam_pan'] = 0
    _servo_angles['cam_tilt'] = 0


def set_motor_speed(motor_id: int, speed: int) -> None:
    """
    Set the speed of an individual motor.
    motor_id: 1 (left), 2 (right)
    speed: -100 to 100
    """
    px = get_picarx()
    px.set_motor_speed(motor_id, speed)

def move_forward(speed: int, duration: float) -> None:
    """
    Move the robot forward at the specified speed for the given duration.
    
    Calibration: At speed 30, moving forward for 1 second goes approximately 30 centimeters.
    
    Args:
        speed (int): Speed percentage from 0 to 100
        duration (float): Duration in seconds
    """
    global _servo_angles
    px = get_picarx()
    px.forward(speed)
    time.sleep(duration)
    px.stop()
    _servo_angles['dir_servo'] = 0

def move_backward(speed: int, duration: float) -> None:
    global _servo_angles
    px = get_picarx()
    px.backward(speed)
    time.sleep(duration)
    px.stop()
    _servo_angles['dir_servo'] = 0

def turn_left(speed: int, duration: float) -> None:
    """Turn left in place using differential motor control with cali_dir_value."""
    global _servo_angles
    px = get_picarx()
    
    # Set motor directions for left turn: left motor backward, right motor forward
    px.cali_dir_value = [-1, 1]  # [left_motor, right_motor] -1=backward, 1=forward
    px.forward(speed)
    time.sleep(duration)
    px.stop()
    # Reset motor directions to normal
    px.cali_dir_value = [1, 1]
    _servo_angles['dir_servo'] = 0

def turn_right(speed: int, duration: float) -> None:
    """Turn right in place using differential motor control with cali_dir_value."""
    global _servo_angles
    px = get_picarx()
    
    # Set motor directions for right turn: left motor forward, right motor backward
    px.cali_dir_value = [1, -1]  # [left_motor, right_motor] -1=backward, 1=forward
    px.forward(speed)
    time.sleep(duration)
    px.stop()
    # Reset motor directions to normal
    px.cali_dir_value = [1, 1]
    _servo_angles['dir_servo'] = 0

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

#function to set the direction servo angle
def set_dir_servo(angle: float) -> None:
    global _servo_angles # call the global variable since we are assigning it a value
    px = get_picarx() # get the picarx object to modify its servo angles object
    if angle > 30:
        angle = 30
    if angle < -30:
        angle = -30
    px.set_dir_servo_angle(angle) # set the direction servo angle
    _servo_angles['dir_servo'] = angle # save the angle to the global variable

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

def get_ultrasound() -> float:
    """Return distance in centimeters from the ultrasonic sensor."""
    px = get_picarx()
    return px.ultrasonic.read()

def get_grayscale() -> list:
    """Return list of grayscale sensor readings (0-4095, left to right)."""
    px = get_picarx()
    return px.get_grayscale_data()

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