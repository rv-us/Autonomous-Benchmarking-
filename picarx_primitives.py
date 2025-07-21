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
from robot_hat import Ultrasonic, GrayscaleModule
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

_ultrasonic = None
def get_ultrasonic() -> Ultrasonic:
    global _ultrasonic
    if _ultrasonic is None:
        _ultrasonic = Ultrasonic("D2", "D3")
    return _ultrasonic

gray_module = None
def get_grayscale() -> GrayscaleModule:
    global gray_module
    if gray_module is None:
        gray_module = GrayscaleModule("A0", "A1", "A2")
    return gray_module

# --- Servo Functions ---
def set_steering(angle: float) -> None:
    """Set the steering servo angle (degrees, -30 to 30 typical)."""
    px = get_picarx()
    px.set_dir_servo_angle(angle)

def set_camera_pan(angle: float) -> None:
    """Set the camera pan servo angle (degrees, -35 to 35 typical)."""
    px = get_picarx()
    px.set_cam_pan_angle(angle)

def set_camera_tilt(angle: float) -> None:
    """Set the camera tilt servo angle (degrees, -35 to 35 typical)."""
    px = get_picarx()
    px.set_cam_tilt_angle(angle)

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
    px = get_picarx()
    px.set_dir_servo_angle(abs(angle))
    px.forward(speed)
    if duration is not None:
        time.sleep(duration)
        px.stop()
        px.set_dir_servo_angle(0)

# --- Sensor Functions ---
def get_ultrasound() -> float:
    """Return distance in centimeters from the ultrasonic sensor."""
    us = get_ultrasonic()
    return us.read()

def get_grayscale() -> List[int]:
    """Return list of grayscale sensor readings (0-100, left to right)."""
    gs = get_grayscale()
    return gs.read()

# --- Camera Function ---
def capture_image(filename: str = "img_capture.jpg") -> None:
    """Capture an image from the camera and save to filename. Requires Vilib to be running."""
    try:
        from vilib import Vilib
        import cv2
        Vilib.camera_start()
        time.sleep(0.2)
        img = Vilib.img
        if img is not None:
            cv2.imwrite(filename, img)
        Vilib.camera_close()
    except Exception as e:
        print(f"Camera error: {e}")

# --- Speaker Function ---
def play_sound(filename: str, volume: int = 100) -> None:
    """Play a sound file through the robot's speaker."""
    music = get_music()
    if os.path.isfile(filename):
        music.sound_play(filename, volume)
    else:
        print(f"Sound file not found: {filename}")

# --- Example Usage ---
if __name__ == "__main__":
    print("Testing Picar-X primitives...")
    set_steering(0)
    set_camera_pan(0)
    set_camera_tilt(0)
    drive_forward(30, 1)
    turn_left(20, 30, 0.5)
    drive_backward(30, 1)
    stop()
    print(f"Ultrasound: {get_ultrasound():.1f} cm")
    print(f"Grayscale: {get_grayscale()}")
    capture_image("test.jpg")
    # play_sound("../sounds/car-double-horn.wav") 