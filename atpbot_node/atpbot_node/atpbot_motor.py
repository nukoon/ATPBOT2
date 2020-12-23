import rclpy
from rclpy.node import Node
import sys
import RPi.GPIO as GPIO 
import time
import geometry_msgs.msg
from std_msgs.msg import String
from pymodbus.client.sync import ModbusSerialClient as ModbusClient

UNIT = 0x1


class DriverSubscriber(Node):
    def __init__(self):
        super().__init__('motor_cmd_vel')
        self.subscription = self.create_subscription(
            geometry_msgs.msg.Twist,
            'cmd_vel',
            self.listener_callback,
            10)
        self.client =  ModbusClient(method='rtu', port='/dev/ttyUSB0', timeout=1, baudrate=115200)
        self.velocity_mode_left = self.client.write_register(8242, 3, unit=UNIT)
        self.motor_enable_left = self.client.write_register(8241, 8, unit=UNIT)
        assert (not self.velocity_mode_left.isError())
        assert (not self.motor_enable_left.isError())
        self.subscription  # prevent unused variable warning
        self.motor_vel1 = self.client.write_register(8250, 0, unit=UNIT)
    def listener_callback(self, msg):
        if msg.linear.x > 0 and msg.linear.x <= 260 : 
            self.motor_vel1 = self.client.write_register(8250, int(msg.linear.x), unit=UNIT)

        if msg.angular.z > 0 and msg.angular.z <= 260:
            print ("Go Left") 

        if msg.linear.x < 0 and msg.linear.x > -260:
            print ("Go Back") 

        if msg.angular.z > -260 and msg.angular.z < 0: 
            print ("Go Right")

        if msg.linear.x == 0 and msg.angular.z == 0:
            print ("Stop!!!") 
            self.motor_vel1 = self.client.write_register(8250, 0, unit=UNIT)
        #self.get_logger().info("x = " , str(msg.linear.x) , " z =" , str(msg.linear.z))



def main(args=None):
    rclpy.init(args=args)
    driver_subscriber = DriverSubscriber()
  
    rclpy.spin(driver_subscriber)

    driver_subscriber.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

