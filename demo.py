from picarx import Picarx
from time import sleep
import readchar

def main():
    px = Picarx()
    speed = 30
    tilt_angle = 0
    pan_angle = 0
    steer_angle = 0

    # Load saved motor direction and steering calibration
    motors_offset = [1, 1]
    px.cali_dir_value = list.copy(motors_offset)

    print("\n--- Picar-X Control Demo ---")
    print("W/S/A/D: Move | U/J/I/K: Camera")
    print("Space:   Stop")
    print("T:       Toggle motor direction and SAVE")
    print("C:       Save current steering angle as center")
    print("Q:       Quit\n")

    try:
        while True:
            key = readchar.readkey().lower()

            if key == 'w':
                px.cali_dir_value = [1, 1]
                px.forward(speed)
            elif key == 's':
                px.cali_dir_value = [-1, -1]
                px.forward(speed)
            elif key == 'a':
                steer_angle = max(-20, steer_angle - 5)
                px.set_dir_servo_angle(steer_angle)
            elif key == 'd':
                steer_angle = min(20, steer_angle + 5)
                px.set_dir_servo_angle(steer_angle)
            elif key == 'u':
                tilt_angle = min(35, tilt_angle + 5)
                px.set_cam_tilt_angle(tilt_angle)
            elif key == 'j':
                tilt_angle = max(-35, tilt_angle - 5)
                px.set_cam_tilt_angle(tilt_angle)
            elif key == 'i':
                pan_angle = max(-35, pan_angle - 5)
                px.set_cam_pan_angle(pan_angle)
            elif key == 'k':
                pan_angle = min(35, pan_angle + 5)
                px.set_cam_pan_angle(pan_angle)
            elif key == ' ':
                px.stop()
                steer_angle = 0
                px.set_dir_servo_angle(0)
            elif key == 't':
                motors_offset[0] *= -1
                motors_offset[1] *= -1
                px.cali_dir_value = list.copy(motors_offset)
                px.motor_direction_calibrate(1, motors_offset[0])
                px.motor_direction_calibrate(2, motors_offset[1])
                print(f"Motor direction saved: {motors_offset}")
            elif key == 'c':
                current_angle = steer_angle
                px.dir_servo_calibrate(current_angle)
                print(f"Steering center saved at angle: {current_angle}")
            elif key == 'q':
                break

            sleep(0.1)

    finally:
        px.stop()
        px.set_dir_servo_angle(0)
        print("Robot stopped. Goodbye!")

if __name__ == "__main__":
    main()

