#!/usr/bin/env python
import rospy
import sys
import os
import struct
import time
import geometry_msgs.msg
from std_msgs.msg import String, Int32, Float32, UInt32
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
from concurrent.futures import ThreadPoolExecutor
from geometry_msgs.msg import Twist

UNIT = 0x1
UNIT2 = 0x3

client_left = ModbusClient(method='rtu', port='/dev/left_motor', timeout=1, baudrate=115200)
client_right = ModbusClient(method='rtu', port='/dev/right_motor', timeout=1, baudrate=115200)
isConnected_left = client_left.connect()
isConnected_right = client_right.connect()

velocity_mode_left = client_left.write_register(8242, 3, unit=UNIT)  # Set Velocity Mode
motor_enable_left = client_left.write_register(8241, 8, unit=UNIT)  # Enable Motor Left
motor_vel1 = client_left.write_register(8250, 0, unit=UNIT)  # Set Velocity = 0 m/s
velocity_mode_right = client_right.write_register(8242, 3, unit=UNIT2)  # Set Velocity Mode
motor_enable_right = client_right.write_register(8241, 8, unit=UNIT2) # Enable Motor Right
motor_vel2 = client_right.write_register(8250, 0, unit=UNIT2) #Set Velocity = 0 m/s
motor_enc_get = client_left.write_register(8197, 1, unit=UNIT)  # Reset Encoder of Left wheel
motor_enc_get2 = client_right.write_register(8197, 1, unit=UNIT2)  # Reset Encoder of Right wheel

assert (not motor_enc_get.isError()) #Checking has any error in encoder
assert (not motor_enc_get2.isError()) #Checking has any error in encoder

assert (not velocity_mode_left.isError()) #Checking has any error in velocity mode of left wheel
assert (not motor_enable_left.isError()) #Checking has any error in motor enable mode of left wheel
assert (not velocity_mode_right.isError()) #Checking has any error in velocity mode of right wheel
assert (not motor_enable_right.isError()) #Checking has any error in motor enable mode of right wheel

class DriverSubscriber():
    def __init__(self):
        rospy.init_node('control_motors')
        rospy.loginfo("Driver subscriber has started")
        
        self.nodename = rospy.get_name()
        self.rate = rospy.get_param("~rate", 50)
        self.base = rospy.get_param("~base_width",0.4807)
        self.max_speed = rospy.get_param("~max_speed",260.0)

        rospy.Subscriber('cmd_vel',Twist,self.listener_callback)
        
        self.left_speed = 0
        self.right_speed = 0
        
        self.dx = 0
        self.dr = 0
        self.dy = 0 

    def listener_callback(self, message):
        """Handle new velocity command message."""
        
        self.dx = message.linear.x
        self.dr = message.angular.z
        self.dy = message.linear.y
        
        #move Forward
        if self.dx > 0 and self.dx <= 260 :
            client_left.write_register(8250, int(self.dx), unit=UNIT)
            client_right.write_register(8250,  self.signed(int(self.dx) * -1), unit=UNIT2)
            print("Forward")
            
        #move Backward    
        elif self.dx < 0 and self.dx >= -260 :
            client_left.write_register(8250, self.signed(int(self.dx)), unit=UNIT)
            client_right.write_register(8250,  self.signed(int(self.dx) * -1), unit=UNIT2)
            print("Backward")
            
        #Stop    
        elif self.dx == 0 and self.dr == 0 :
            client_left.write_register(8250, 0 , unit=UNIT)
            client_right.write_register(8250,  0 , unit=UNIT2)
            print("Stop")
            
        #Turn Left
        elif self.dr > 0 and self.dr <= 260 :
            client_left.write_register(8250, self.signed(int(self.dr) * -1), unit=UNIT)
            client_right.write_register(8250,  self.signed(int(self.dr) * -1), unit=UNIT2)
            print("Turn Left")
            
        #Turn Right
        elif self.dr < 0 and self.dr >= -260 :            
            client_left.write_register(8250, self.signed(int(self.dr) * -1), unit=UNIT)
            client_right.write_register(8250, self.signed(int(self.dr) * -1), unit=UNIT2)
            print("Turn Right")


    def signed(self, value):
        packval = struct.pack('<h', value)
        return struct.unpack('<H', packval)[0]
        

class RightPublisher():
    global client_left, client_right, motor_vel1, motor_vel2

    def __init__(self):
        rospy.loginfo("Right motor wheel has started")
        self.pub = rospy.Publisher('enc_right',Int32, queue_size = 10)
        self.rate = rospy.Rate(10) #10Hz for publisher
    
    def timer (self):
        motor_enc_get = (client_right.read_holding_registers(8234, 2, unit=UNIT2))
        value = Int32()
        value.data = abs((int(motor_enc_get.registers[1]))-65535)
        self.pub.publish(value)
        self.rate.sleep()
        
class LeftPublisher():
    global client_left, client_right, motor_vel1, motor_vel2

    def __init__(self):
        rospy.loginfo("Left motor wheel has started")
        self.pub = rospy.Publisher('enc_left',Int32, queue_size = 10)
        self.rate = rospy.Rate(10) # 10 Hz rate
        
    def timer (self):
        motor_enc_get = client_left.read_holding_registers(8234, 2, unit=UNIT)
        value = Int32()
        value.data = int(motor_enc_get.registers[1])
        self.pub.publish(value)
        self.rate.sleep()
        
class ThreadExecutor() :

    def __init__(self) :
        self.high_priority_nodes = set()
        self.hp_executor = ThreadPoolExecutor (max_workers = os.cpu_count())
        self.lp_executor = ThreadPoolExecutor (max_workers = 1 )
    
    def add_high_priority_node (self,node) :
        self.high_priority_nodes.add (node)    
        
def main():
    driver_subscriber = DriverSubscriber()
    enc_left_node = LeftPublisher()
    enc_right_node = RightPublisher()
    executor = ThreadExecutor()
       
    while not rospy.is_shutdown():
        executor.add_high_priority_node (driver_subscriber)
        executor.add_high_priority_node (enc_left_node)
        executor.add_high_priority_node (enc_right_node)
        executor.add_high_priority_node (enc_left_node.timer())
        executor.add_high_priority_node (enc_right_node.timer())

if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        pass
