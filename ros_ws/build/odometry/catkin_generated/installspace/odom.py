#!/usr/bin/env python3

import rospy
import roslib
from tf.broadcaster import TransformBroadcaster
from nav_msgs.msg import Odometry
import math
from math import sin,cos,pi
from geometry_msgs.msg import Point, Pose, Quaternion, Twist, Vector3 , TransformStamped
from std_msgs.msg import Int32
import time
from tf.transformations import euler_from_quaternion

class DifferentialDriveTF() :
    def __init__ (self) :
        rospy.init_node("odometry_robot")
        rospy.loginfo("Odometry Started")
        self.nodename = rospy.get_name()

        ### Parameters ###
        self.rate = rospy.get_param('~rate',50.0)
        self.ticks_meter = float(rospy.get_param('ticks_meter',7669))
        self.base_width = float(rospy.get_param('~base_width',0.4807))
        
        self.base_frame_id = rospy.get_param('~base_frame_id','base_link')
        self.odom_frame_id = rospy.get_param('~odom_frame_id','odom')
        self.encoder_min = rospy.get_param('~encoder_min',0.0)
        self.encoder_max = rospy.get_param('~encoder_max',65535.0)
        self.encoder_low_wrap = rospy.get_param('wheel_low_wrap', (self.encoder_max - self.encoder_min) * 0.3 + self.encoder_min )
        self.encoder_high_wrap = rospy.get_param('wheel_high_wrap', (self.encoder_max - self.encoder_min) * 0.7 + self.encoder_min )

        self.t_delta = rospy.Duration(1.0/self.rate)
        self.t_next =  rospy.Time.now() + self.t_delta

        #internal data from wheel encoder
        self.enc_left = None
        self.enc_right = None
        self.left = 0
        self.right = 0
        self.lmult = 0
        self.rmult = 0
        self.prev_lencoder = 0
        self.prev_rencoder = 0
        self.x = 0
        self.y = 0
        self.th = 0
        self.dx = 0
        self.dr = 0 
        self.then = rospy.Time.now()
        
        #Subscriptions
        rospy.Subscriber('enc_left' , Int32 , self.leftTicksCallback)
        rospy.Subscriber('enc_right' , Int32 , self.rightTicksCallback)
        self.odom_pub = rospy.Publisher("odom" , Odometry , queue_size=50)
        self.odom_broadcaster = TransformBroadcaster()

    #Callback function of left_encoder and right_encoder
    def leftTicksCallback(self,msg):
        enc = msg.data
        if(enc < self.encoder_low_wrap and self.prev_lencoder > self.encoder_high_wrap):
            self.lmult = self.lmult + 1
        
        if(enc > self.encoder_high_wrap and self.prev_lencoder < self.encoder_low_wrap):
            self.lmult = self.lmult - 1
    
        self.left = 1.0 * (enc + self.lmult * (self.encoder_max - self.encoder_min))
        self.prev_lencoder = enc
        
    
    def rightTicksCallback(self,msg):
        enc = msg.data 
        if(enc < self.encoder_high_wrap and self.prev_rencoder > self.encoder_high_wrap):
            self.rmult = self.rmult + 1
    
        if(enc > self.encoder_high_wrap and self.prev_rencoder < self.encoder_low_wrap):
            self.rmult = self.rmult - 1
            
        self.right = 1.0 * (enc + self.rmult *(self.encoder_max - self.encoder_min))
        self.prev_rencoder = enc


    def update (self):
        now = rospy.Time.now()
        if(now > self.t_next) :
            elapsed = now - self.then
            self.then = now
            elapsed = elapsed.to_sec()
        
            #calculate Odometry of robot
            if self.enc_left == None :
                d_left = 0
                d_right = 0
        
            else:
                d_left = (self.left - self.enc_left) / self.ticks_meter
                d_right = (self.right - self.enc_right) / self.ticks_meter
            
            self.enc_left = self.left
            self.enc_right = self.right
        
            #distance traveled is the average of the two wheels
            d = (d_left + d_right) / 2
        
            #this approximation works (in radians) for small angles
            dth = (d_right - d_left) / self.base_width
        
            #calculate velocities
            self.dx = d / elapsed
            self.dr = dth / elapsed
        
            if (d != 0):
                #calculate distance traveled in x and y 
                x = cos (dth) * d
                y = -sin (dth) * d
            
                #calculate the final position of the robot
                self.x = self.x + (cos(self.th) * x - sin(self.th) * y)
                self.y = self.y + (sin(self.th) * x + cos(self.th) * y)
        
            if (dth != 0):
                self.th = self.th + dth
    
            #publish the odom information
            quaternion = Quaternion()
            quaternion.x = 0.0
            quaternion.y = 0.0
            quaternion.z = sin (self.th/2)
            quaternion.w = cos (self.th/2)
            
            """Change from Quaternion to Euler"""
            #quaternion_list = [quaternion.x,quaternion.y,quaternion.z,quaternion.w]    
            #euler = euler_from_quaternion(quaternion_list)
        
            self.odom_broadcaster.sendTransform(
                (self.x,self.y,0),
                (quaternion.x,quaternion.y,quaternion.z,quaternion.w),
                rospy.Time.now(),
                self.base_frame_id,
                self.odom_frame_id
                )
            odom = Odometry()
            odom.header.stamp = now
            odom.header.frame_id = self.odom_frame_id
            odom.pose.pose.position.x = self.x
            odom.pose.pose.position.y = self.y
            odom.pose.pose.position.z = 0.0
            odom.pose.pose.orientation = quaternion
            odom.child_frame_id = self.base_frame_id
            odom.twist.twist.linear.x = self.dx
            odom.twist.twist.linear.y = 0.0
            odom.twist.twist.angular.z = self.dr
            self.odom_pub.publish(odom)
        
if __name__ == "__main__":
    try:
        diff_tf = DifferentialDriveTF()
        while not rospy.is_shutdown():
            diff_tf.update()
 
    except rospy.ROSInterruptException:
        pass
