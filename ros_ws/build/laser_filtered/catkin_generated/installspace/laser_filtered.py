#!/usr/bin/env python3
import rospy
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Float32
from math import pi

class LaserScanFiltered:
    
    def __init__ (self) :
        rospy.init_node("laser_filters")
        rospy.loginfo("Laser has been filtered")
        self.laser = LaserScan()
        self.nodename = rospy.get_name()
        
        #Parameters#
        self.rate = rospy.get_param("~rate",50.0)
        
        self.laser_frame_id = rospy.get_param("~base_scan_id","laser_frame")
        
        #internal data form scan
        self.scan = []
        self.scan_filtered = []
        
        #Subscription
        rospy.Subscriber("/scan",LaserScan,self.LaserScanCallBack)
        
        #Publisher
        self.laser_pub = rospy.Publisher("scan_filtered",LaserScan,queue_size=50)
        rospy.spin()
        
    def LaserScanCallBack( self , msg ):
        self.laser = msg
        count = len(self.laser.ranges)
        self.laser.ranges = self.laser.ranges[0:int(count/2)]
        self.laser_pub.publish(self.laser)
        
        
if __name__ == "__main__":
    while not rospy.is_shutdown():
        try:
            laser = LaserScanFiltered()
        except rospy.ROSInterruptException:
            pass
