# PicarX and Robot-HAT Functions Documentation

This document provides comprehensive documentation for all available functions from the `picarx` and `robot_hat` libraries used in the SunFounder Picar-X robot project.

## Table of Contents
1. [PicarX Class Functions](#picarx-class-functions)
2. [Robot-HAT Library Functions](#robot-hat-library-functions)
3. [Vilib Camera Functions](#vilib-camera-functions)
4. [Function Categories](#function-categories)

---

## PicarX Class Functions

### Movement Control

#### `forward(speed: int) -> None`
**Description:** Moves the robot forward at the specified speed.
- **Parameters:**
  - `speed` (int): Speed percentage from 0 to 100
- **Usage:**
  ```python
  px = Picarx()
  px.forward(80)  # Move forward at 80% speed
  ```

#### `backward(speed: int) -> None`
**Description:** Moves the robot backward at the specified speed.
- **Parameters:**
  - `speed` (int): Speed percentage from 0 to 100
- **Usage:**
  ```python
  px.backward(50)  # Move backward at 50% speed
  ```

#### `stop() -> None`
**Description:** Stops all robot movement immediately.
- **Usage:**
  ```python
  px.stop()  # Stop all motors
  ```

#### `set_motor_speed(motor_id: int, speed: int) -> None`
**Description:** Sets the speed of an individual motor.
- **Parameters:**
  - `motor_id` (int): Motor ID (1 = left motor, 2 = right motor)
  - `speed` (int): Speed from -100 to 100 (negative = reverse)
- **Usage:**
  ```python
  px.set_motor_speed(1, 50)   # Left motor forward at 50%
  px.set_motor_speed(2, -30)  # Right motor backward at 30%
  ```

### Servo Control

#### `set_dir_servo_angle(angle: float) -> None`
**Description:** Sets the steering servo angle for directional control.
- **Parameters:**
  - `angle` (float): Angle in degrees (-30 to 30 typical range)
- **Usage:**
  ```python
  px.set_dir_servo_angle(30)   # Turn right
  px.set_dir_servo_angle(-30)  # Turn left
  px.set_dir_servo_angle(0)    # Go straight
  ```

#### `set_cam_pan_angle(angle: float) -> None`
**Description:** Sets the camera pan (left/right) servo angle.
- **Parameters:**
  - `angle` (float): Angle in degrees (-35 to 35 typical range)
- **Usage:**
  ```python
  px.set_cam_pan_angle(20)   # Pan camera right
  px.set_cam_pan_angle(-20)  # Pan camera left
  ```

#### `set_cam_tilt_angle(angle: float) -> None`
**Description:** Sets the camera tilt (up/down) servo angle.
- **Parameters:**
  - `angle` (float): Angle in degrees (-35 to 35 typical range)
- **Usage:**
  ```python
  px.set_cam_tilt_angle(15)   # Tilt camera up
  px.set_cam_tilt_angle(-15)  # Tilt camera down
  ```

### Sensor Functions

#### `ultrasonic.read() -> float`
**Description:** Reads distance from the ultrasonic sensor.
- **Returns:** Distance in centimeters
- **Usage:**
  ```python
  distance = px.ultrasonic.read()
  print(f"Distance: {distance} cm")
  ```

#### `get_grayscale_data() -> list`
**Description:** Gets grayscale sensor readings for line following.
- **Returns:** List of 3 grayscale values (0-4095, left to right)
- **Usage:**
  ```python
  grayscale_values = px.get_grayscale_data()
  print(f"Grayscale: {grayscale_values}")  # [left, center, right]
  ```

#### `get_line_status(val_list: list) -> list`
**Description:** Determines line status from grayscale values.
- **Parameters:**
  - `val_list` (list): List of 3 grayscale values
- **Returns:** List of 3 booleans [left, center, right] (True = background, False = line)
- **Usage:**
  ```python
  grayscale = px.get_grayscale_data()
  line_status = px.get_line_status(grayscale)
  # [True, False, True] means line detected in center sensor
  ```

#### `get_cliff_status(val_list: list) -> bool`
**Description:** Detects if robot is at a cliff edge.
- **Parameters:**
  - `val_list` (list): List of 3 grayscale values
- **Returns:** True if cliff detected, False if safe
- **Usage:**
  ```python
  grayscale = px.get_grayscale_data()
  is_cliff = px.get_cliff_status(grayscale)
  ```

### Calibration Functions

#### `set_line_reference(refs: list) -> None`
**Description:** Sets reference values for line following calibration.
- **Parameters:**
  - `refs` (list): List of 3 reference values for [left, center, right] sensors
- **Usage:**
  ```python
  px.set_line_reference([1400, 1400, 1400])
  ```

#### `set_cliff_reference(refs: list) -> None`
**Description:** Sets reference values for cliff detection calibration.
- **Parameters:**
  - `refs` (list): List of 3 reference values for [left, center, right] sensors
- **Usage:**
  ```python
  px.set_cliff_reference([200, 200, 200])
  ```

#### `dir_servo_calibrate(offset: float) -> None`
**Description:** Calibrates the direction servo with an offset value.
- **Parameters:**
  - `offset` (float): Calibration offset in degrees
- **Usage:**
  ```python
  px.dir_servo_calibrate(-2.5)  # Apply -2.5 degree offset
  ```

#### `cam_pan_servo_calibrate(offset: float) -> None`
**Description:** Calibrates the camera pan servo with an offset value.
- **Parameters:**
  - `offset` (float): Calibration offset in degrees
- **Usage:**
  ```python
  px.cam_pan_servo_calibrate(1.2)  # Apply 1.2 degree offset
  ```

#### `cam_tilt_servo_calibrate(offset: float) -> None`
**Description:** Calibrates the camera tilt servo with an offset value.
- **Parameters:**
  - `offset` (float): Calibration offset in degrees
- **Usage:**
  ```python
  px.cam_tilt_servo_calibrate(-0.8)  # Apply -0.8 degree offset
  ```

#### `motor_direction_calibrate(motor_id: int, direction: int) -> None`
**Description:** Calibrates motor direction (forward/backward).
- **Parameters:**
  - `motor_id` (int): Motor ID (1 or 2)
  - `direction` (int): Direction multiplier (1 or -1)
- **Usage:**
  ```python
  px.motor_direction_calibrate(1, -1)  # Reverse left motor direction
  ```

### Calibration Properties

#### `dir_cali_val` (property)
**Description:** Current calibration value for direction servo.
- **Type:** float
- **Usage:**
  ```python
  current_offset = px.dir_cali_val
  px.dir_cali_val = -2.5  # Set new offset
  ```

#### `cam_pan_cali_val` (property)
**Description:** Current calibration value for camera pan servo.
- **Type:** float
- **Usage:**
  ```python
  current_offset = px.cam_pan_cali_val
  ```

#### `cam_tilt_cali_val` (property)
**Description:** Current calibration value for camera tilt servo.
- **Type:** float
- **Usage:**
  ```python
  current_offset = px.cam_tilt_cali_val
  ```

#### `cali_dir_value` (property)
**Description:** Current calibration values for motor directions.
- **Type:** list
- **Usage:**
  ```python
  motor_directions = px.cali_dir_value  # [left_motor, right_motor]
  ```

---

## Robot-HAT Library Functions

### Music Class

#### `Music()`
**Description:** Creates a music/sound player instance.
- **Usage:**
  ```python
  from robot_hat import Music
  music = Music()
  ```

#### `sound_play(filename: str, volume: int = 100) -> None`
**Description:** Plays a sound file synchronously (blocks until finished).
- **Parameters:**
  - `filename` (str): Path to sound file (.wav, .mp3, etc.)
  - `volume` (int): Volume level 0-100 (default: 100)
- **Usage:**
  ```python
  music.sound_play("sounds/horn.wav", 80)
  ```

#### `sound_play_threading(filename: str, volume: int = 100) -> None`
**Description:** Plays a sound file asynchronously (non-blocking).
- **Parameters:**
  - `filename` (str): Path to sound file
  - `volume` (int): Volume level 0-100 (default: 100)
- **Usage:**
  ```python
  music.sound_play_threading("sounds/engine.wav", 50)
  ```

### Ultrasonic Class

#### `Ultrasonic(trig_pin, echo_pin)`
**Description:** Creates an ultrasonic sensor instance.
- **Parameters:**
  - `trig_pin`: Trigger pin object
  - `echo_pin`: Echo pin object
- **Usage:**
  ```python
  from robot_hat import Ultrasonic, Pin
  trig = Pin("P9")
  echo = Pin("P10")
  ultrasonic = Ultrasonic(trig, echo)
  ```

#### `read(times: int = 1) -> float`
**Description:** Reads distance from ultrasonic sensor.
- **Parameters:**
  - `times` (int): Number of readings to average (default: 1)
- **Returns:** Distance in centimeters
- **Usage:**
  ```python
  distance = ultrasonic.read(5)  # Average of 5 readings
  ```

### Pin Class

#### `Pin(pin_name: str)`
**Description:** Creates a GPIO pin object.
- **Parameters:**
  - `pin_name` (str): Pin name (e.g., "P9", "P10", "LED")
- **Usage:**
  ```python
  from robot_hat import Pin
  led = Pin('LED')
  ```

### Servo Class

#### `Servo(servo_id: int)`
**Description:** Creates a servo control instance.
- **Parameters:**
  - `servo_id` (int): Servo ID (0-11)
- **Usage:**
  ```python
  from robot_hat import Servo
  servo = Servo(0)
  ```

#### `angle(angle: float) -> None`
**Description:** Sets servo angle.
- **Parameters:**
  - `angle` (float): Angle in degrees
- **Usage:**
  ```python
  servo.angle(45)  # Set servo to 45 degrees
  ```

### Utility Functions

#### `reset_mcu() -> None`
**Description:** Resets the microcontroller unit.
- **Usage:**
  ```python
  from robot_hat.utils import reset_mcu
  reset_mcu()
  ```

---

## Vilib Camera Functions

### Camera Control

#### `Vilib.camera_start(vflip: bool = False, hflip: bool = False) -> None`
**Description:** Starts the camera system.
- **Parameters:**
  - `vflip` (bool): Vertical flip (default: False)
  - `hflip` (bool): Horizontal flip (default: False)
- **Usage:**
  ```python
  from vilib import Vilib
  Vilib.camera_start(vflip=False, hflip=False)
  ```

#### `Vilib.camera_close() -> None`
**Description:** Closes the camera system.
- **Usage:**
  ```python
  Vilib.camera_close()
  ```

#### `Vilib.display(local: bool = True, web: bool = True) -> None`
**Description:** Starts camera display (local and/or web).
- **Parameters:**
  - `local` (bool): Show local display (default: True)
  - `web` (bool): Enable web display (default: True)
- **Usage:**
  ```python
  Vilib.display(local=False, web=True)
  ```

#### `Vilib.show_fps() -> None`
**Description:** Shows FPS counter on display.
- **Usage:**
  ```python
  Vilib.show_fps()
  ```

### Image Capture

#### `Vilib.take_photo(name: str, path: str) -> None`
**Description:** Takes a photo and saves it.
- **Parameters:**
  - `name` (str): Photo name (without extension)
  - `path` (str): Save directory path
- **Usage:**
  ```python
  Vilib.take_photo("my_photo", "/home/pi/Pictures/")
  ```

### Computer Vision

#### `Vilib.color_detect(color: str) -> None`
**Description:** Enables color detection for specified color.
- **Parameters:**
  - `color` (str): Color to detect ('red', 'blue', 'green', etc.)
- **Usage:**
  ```python
  Vilib.color_detect('red')
  ```

#### `Vilib.face_detect_switch(flag: bool) -> None`
**Description:** Enables or disables face detection.
- **Parameters:**
  - `flag` (bool): True to enable, False to disable
- **Usage:**
  ```python
  Vilib.face_detect_switch(True)
  ```

#### `Vilib.qrcode_detect_switch(flag: bool) -> None`
**Description:** Enables or disables QR code detection.
- **Parameters:**
  - `flag` (bool): True to enable, False to disable
- **Usage:**
  ```python
  Vilib.qrcode_detect_switch(True)
  ```

### Camera Properties

#### `Vilib.img` (property)
**Description:** Current camera image (OpenCV format).
- **Type:** numpy.ndarray
- **Usage:**
  ```python
  import cv2
  if Vilib.img is not None:
      cv2.imwrite("capture.jpg", Vilib.img)
  ```

#### `Vilib.flask_start` (property)
**Description:** Indicates if web server is running.
- **Type:** bool
- **Usage:**
  ```python
  while not Vilib.flask_start:
      time.sleep(0.01)
  ```

---

## Function Categories

### Movement Functions
- `forward()`, `backward()`, `stop()`
- `set_motor_speed()`
- `set_dir_servo_angle()`

### Camera Functions
- `set_cam_pan_angle()`, `set_cam_tilt_angle()`
- `Vilib.camera_start()`, `Vilib.camera_close()`
- `Vilib.take_photo()`, `Vilib.display()`

### Sensor Functions
- `ultrasonic.read()`
- `get_grayscale_data()`
- `get_line_status()`, `get_cliff_status()`

### Audio Functions
- `Music.sound_play()`, `Music.sound_play_threading()`

### Calibration Functions
- `set_line_reference()`, `set_cliff_reference()`
- `dir_servo_calibrate()`, `cam_pan_servo_calibrate()`, `cam_tilt_servo_calibrate()`
- `motor_direction_calibrate()`

### Computer Vision Functions
- `Vilib.color_detect()`, `Vilib.face_detect_switch()`, `Vilib.qrcode_detect_switch()`

---

## Usage Examples

### Basic Movement
```python
from picarx import Picarx
import time

px = Picarx()

# Move forward
px.forward(50)
time.sleep(2)
px.stop()

# Turn left
px.set_dir_servo_angle(-30)
px.forward(30)
time.sleep(1)
px.stop()
px.set_dir_servo_angle(0)
```

### Sensor Reading
```python
# Read distance
distance = px.ultrasonic.read()
print(f"Distance: {distance} cm")

# Read grayscale sensors
grayscale = px.get_grayscale_data()
line_status = px.get_line_status(grayscale)
print(f"Line detected: {line_status}")
```

### Camera Control
```python
from vilib import Vilib

# Start camera
Vilib.camera_start()
Vilib.display(local=False, web=True)

# Take photo
Vilib.take_photo("my_photo", "/home/pi/Pictures/")

# Close camera
Vilib.camera_close()
```

### Sound Playback
```python
from robot_hat import Music

music = Music()
music.sound_play("sounds/horn.wav", 80)
music.sound_play_threading("sounds/engine.wav", 50)
```

This documentation covers all the major functions available in the PicarX and Robot-HAT libraries. For more detailed information, refer to the official SunFounder documentation and examples.
