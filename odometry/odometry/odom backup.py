from concurrent.futures import ThreadPoolExecutor
import rclpy
from rclpy.executors import Executor
from rclpy.node import Node
import sys
import RPi.GPIO as GPIO 
import time
import os, sys, select, termios, tty
import threading
import geometry_msgs.msg

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

class OdomPublisher(Node):

    def __init__(self):
        super().__init__('odom_publisher')
        self.publisher_ = self.create_publisher(geometry_msgs.msg.Pose, 'odom', 10)
        timer_period = 0.0001  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.i = 0
        self.aEncoder_right_pin = 17
        self.bEncoder_right_pin = 27
        self.aEncoder_left_pin = 3
        self.bEncoder_left_pin = 2
        self.state_right_A =0
        self.state_left_A =0
        self.state_right_A =0
        self.state_left_A =0
        self.counter_right = 0
        self.counter_left = 0
   
        GPIO.setup(self.aEncoder_right_pin, GPIO.IN)
        GPIO.setup(self.bEncoder_right_pin, GPIO.IN)
        GPIO.setup(self.aEncoder_left_pin, GPIO.IN)
        GPIO.setup(self.bEncoder_left_pin, GPIO.IN)

        self.aright_LastState = GPIO.input(self.aEncoder_right_pin)
        self.aleft_LastState = GPIO.input(self.aEncoder_left_pin)


    def timer_callback(self):
        
        self.state_right_A = GPIO.input(self.aEncoder_right_pin)
#        self.state_left_A = GPIO.input(self.aEncoder_left_pin)
        if self.state_right_A != self.aright_LastState:
            if GPIO.input(self.bEncoder_right_pin) != self.state_right_A:
                self.counter_right +=1
            else:
                self.counter_right -= 1
        self.aright_LastState = self.state_right_A      
#        if self.state_left_A != self.aleft_LastState:
#            if GPIO.input(self.bEncoder_left_pin) != self.state_left_A:
#                self.counter_left -=1
#            else:
#                self.counter_left += 1
#        self.aleft_LastState = self.state_left_A
        msg = geometry_msgs.msg.Pose()
        msg.position.x = float(self.counter_right)
        msg.position.y = float(self.counter_left)
        msg.position.z = float(self.i)
        self.publisher_.publish(msg)
        if self.i > 10000:
            self.i = 0
        self.i += 1 
        #self.get_logger().info('Publishing: "%d"' % msg.position.x)


def main(args=None):
    rclpy.init(args=args)
    odom_publisher = OdomPublisher()

    rclpy.spin(odom_publisher)
    
    odom_publisher.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
