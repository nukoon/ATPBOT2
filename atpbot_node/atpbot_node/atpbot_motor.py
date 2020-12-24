#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import sys
import struct
import RPi.GPIO as GPIO 
import time
import geometry_msgs.msg
from std_msgs.msg import String, Int32
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
from concurrent.futures import ThreadPoolExecutor
from rclpy.executors import Executor

UNIT = 0x1

client =  ModbusClient(method='rtu', port='/dev/ttyUSB0', timeout=1, baudrate=115200)
isConnected = client.connect()

print(isConnected)
motor_vel1 = client.write_register(8250, 0, unit=UNIT)
velocity_mode_left = client.write_register(8242, 3, unit=UNIT)
motor_enable_left = client.write_register(8241, 8, unit=UNIT)
assert (not velocity_mode_left.isError())
assert (not motor_enable_left.isError())
class DriverSubscriber(Node):
    def __init__(self):
        super().__init__('motor_cmd_vel')
        self.subscription = self.create_subscription(
            geometry_msgs.msg.Twist,
            'cmd_vel',
            self.listener_callback,
            10)

    def signed(self, value):
        packval = struct.pack('<h',value)
        return struct.unpack('<H',packval)[0]

    def listener_callback(self, msg):
        global client, motor_vel1
        if msg.linear.x > 0 and msg.linear.x <= 260 : 
            print ("Go forward") 
            motor_vel1 = client.write_register(8250, int(msg.linear.x), unit=UNIT)

        if msg.angular.z > 0 and msg.angular.z <= 260:
            print ("Go Left") 

        if msg.linear.x < 0 and msg.linear.x > -260:
            motor_vel1 = client.write_register(8250, self.signed(int(msg.linear.x)), unit=UNIT)
            print ("Go Back") 
	
        if msg.angular.z > -260 and msg.angular.z < 0: 
            print ("Go Right")

        if msg.linear.x == 0 and msg.angular.z == 0:
            print ("Stop!!!") 
            motor_vel1 = client.write_register(8250, 0, unit=UNIT)
        #self.get_logger().info("x = " , str(msg.linear.x) , " z =" , str(msg.linear.z))

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
    global client, motor_vel1
    def __init__(self):
        super().__init__('Enc_right_Sub')
        self.subscription = self.create_subscription(
            Int32,
            'enc_right',
            self.listener_callback,
            10)
        self.subscription  # prevent unused variable warning

    def listener_callback(self, msg):
        global client, motor_vel1
        motor_enc_get = client.read_holding_registers(8234, 2, unit=UNIT)
        value = Int32()
        value.data = int(motor_enc_get.registers[1])

class LeftSubscriber(Node):
    def __init__(self):
        super().__init__('Enc_left_Sub')
        self.subscription = self.create_subscription(
            Int32,
            'enc_left',
            self.listener_callback,
            10)
        self.subscription  # prevent unused variable warning
        self.lastEnc = 0

    def listener_callback(self, msg):
        motor_enc_get = client.read_holding_registers(8234, 2, unit=UNIT)
        value = Int32()
        value.data = int(motor_enc_get.registers[1])

def main(args=None):
    rclpy.init(args=args)
    driver_subscriber = DriverSubscriber()
    enc_left_node = LeftSubscriber()
    enc_right_node = RightSubscriber()

    executor = PriorityExecutor()
    executor.add_high_priority_node(driver_subscriber)
    executor.add_node(enc_left_node)
    executor.add_node(enc_right_node)

    executor.spin()

    driver_subscriber.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

