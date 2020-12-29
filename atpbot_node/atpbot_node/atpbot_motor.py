#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import sys, os
import struct
#import RPi.GPIO as GPIO
import time
import geometry_msgs.msg
from std_msgs.msg import String, Int32
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
from concurrent.futures import ThreadPoolExecutor
from rclpy.executors import Executor

UNIT = 0x1
UNIT2 = 0x3

client_left = ModbusClient(method='rtu', port='/dev/ttyUSB0', timeout=1, baudrate=115200)
client_right = ModbusClient(method='rtu', port='/dev/ttyUSB1', timeout=1, baudrate=115200)
isConnected_left = client_left.connect()
isConnected_right = client_right.connect()



velocity_mode_left = client_left.write_register(8242, 3, unit=UNIT)
motor_enable_left = client_left.write_register(8241, 8, unit=UNIT)
motor_vel1 = client_left.write_register(8250, 0, unit=UNIT)
velocity_mode_right = client_right.write_register(8242, 3, unit=UNIT2)
motor_enable_right = client_right.write_register(8241, 8, unit=UNIT2)
motor_vel2 = client_right.write_register(8250, 0, unit=UNIT2)

assert (not velocity_mode_left.isError())
assert (not motor_enable_left.isError())
<<<<<<< HEAD
=======
assert (not velocity_mode_right.isError())
assert (not motor_enable_right.isError())

print(isConnected_left)
print(isConnected_right)
>>>>>>> badfac416af5ab4158ec6737d9c3638ecc4153a4

class DriverSubscriber(Node):
    def __init__(self):
        super().__init__('motor_cmd_vel')
        self.subscription = self.create_subscription(
            geometry_msgs.msg.Twist,
            'cmd_vel',
            self.listener_callback,
            10)
        self.direction = ""
        self.old_cmd = 0

    def signed(self, value):
        packval = struct.pack('<h', value)
        return struct.unpack('<H', packval)[0]

    def listener_callback(self, msg):
        global client_left , client_right , motor_vel1 , motor_vel2
        if msg.linear.x > 0 and msg.linear.x <= 260:
            print("Go forward")
            self.direction = "forward"
            self.old_cmd =  msg.linear.x
            motor_vel1 = client_left.write_register(8250, int(msg.linear.x), unit=UNIT)
            motor_vel2 = client_right.write_register(8250, self.signed(int(msg.linear.x * -1)), unit=UNIT2)

        if msg.angular.z > 0 and msg.angular.z <= 260:
            motor_vel1 = client_left.write_register(8250, self.signed(int(msg.angular.z * -1)), unit=UNIT)
            motor_vel2 = client_right.write_register(8250, self.signed(int(msg.angular.z * -1)), unit=UNIT2)
            print("Go Left")
            self.direction = "left"
            self.old_cmd =  msg.angular.z

        if msg.linear.x < 0 and msg.linear.x > -260:
            motor_vel1 = client_left.write_register(8250, self.signed(int(msg.linear.x)), unit=UNIT)
            motor_vel2 = client_right.write_register(8250,  self.signed(int(msg.linear.x * -1)), unit=UNIT2)
            print("Go Back")
            self.direction = "back"
            self.old_cmd =  msg.linear.x

        if msg.angular.z > -260 and msg.angular.z < 0:
            motor_vel1 = client_left.write_register(8250, self.signed(int(msg.angular.z * -1)), unit=UNIT)
            motor_vel2 = client_right.write_register(8250, self.signed(int(msg.angular.z * -1)), unit=UNIT2)
            self.direction = "right"
            self.old_cmd =  msg.angular.z
            print("Go Right")

        if msg.linear.x == 0 and msg.angular.z == 0:
            print("Process Stopping")
            i = 20
            while i > 0:
                if self.direction = "forward":
                    motor_vel1 = client_left.write_register(8250, int(i), unit=UNIT)
                    motor_vel2 = client_right.write_register(8250, self.signed(int(i * -1)), unit=UNIT2)
                elif self.direction = "back":
                    motor_vel1 = client_left.write_register(8250, int(i * -1), unit=UNIT)
                    motor_vel2 = client_right.write_register(8250, self.signed(int(i)), unit=UNIT2)
                i -= 2
            motor_vel1 = client_left.write_register(8250, 0, unit=UNIT)
            motor_vel2 = client_right.write_register(8250, 0, unit=UNIT2)
            print("Stoped!!!")
        # self.get_logger().info("x = " , str(msg.linear.x) , " z =" , str(msg.linear.z))


class PriorityExecutor(Executor):
    def __init__(self):
        super().__init__()
        self.high_priority_nodes = set()
        self.hp_executor = ThreadPoolExecutor(max_workers=os.cpu_count() or 4)
        self.lp_executor = ThreadPoolExecutor(max_workers=1)

    def add_high_priority_node(self, node):
        self.high_priority_nodes.add(node)
        # add_node inherited
        self.add_node(node)

    def spin_once(self, timeout_sec=None):
        # wait_for_ready_callbacks yields callbacks that are ready to be executed
        try:
            handler, group, node = self.wait_for_ready_callbacks(timeout_sec=timeout_sec)

        except StopIteration:
            pass
        else:
            if node in self.high_priority_nodes:
                self.hp_executor.submit(handler)
            else:
                self.lp_executor.submit(handler)


class RightSubscriber(Node):
    global client_left , client_right , motor_vel1 , motor_vel2

    def __init__(self):
        super().__init__('Enc_right_Pub')
        self.publisher_ = self.create_publisher(Int32, 'enc_right', 10)
        timer_period = 0.001  # seconds
        self.timer = self.create_timer(timer_period, self.publisher_callback)

    def publisher_callback(self):
        global client_left , client_right , motor_vel1 , motor_vel2
        motor_enc_get = client_right.read_holding_registers(8234, 2, unit=UNIT)
        value = Int32()
        value.data = int(motor_enc_get.registers[1])
        self.publisher_.publish(value)


class LeftSubscriber(Node):
    global client_left , client_right , motor_vel1 , motor_vel2

    def __init__(self):
        super().__init__('Enc_left_Pub')
        self.publisher_ = self.create_publisher(Int32, 'enc_left', 10)
        timer_period = 0.001  # seconds
        self.timer = self.create_timer(timer_period, self.publisher_callback)

    def publisher_callback(self):
        global client_left , client_right , motor_vel1 , motor_vel2
        motor_enc_get = client_left.read_holding_registers(8234, 2, unit=UNIT)
        value = Int32()
        value.data = int(motor_enc_get.registers[1])
        self.publisher_.publish(value)


def main(args=None):
    rclpy.init(args=args)
    driver_subscriber = DriverSubscriber()
    #enc_left_node = LeftSubscriber()
    #enc_right_node = RightSubscriber()

    executor = PriorityExecutor()
    executor.add_high_priority_node(driver_subscriber)
    #executor.add_node(enc_left_node)
    #executor.add_node(enc_right_node)

    executor.spin()

    driver_subscriber.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
