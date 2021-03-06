#!/usr/bin/env python

import rospy
from geometry_msgs.msg import PoseWithCovarianceStamped
from tf.transformations import quaternion_from_euler

def pub_init_pose():
    rospy.init_node('init_pos')
    pub = rospy.Publisher('/initialpose', PoseWithCovarianceStamped, queue_size = 10)
    rospy.sleep(5)
    checkpoint = PoseWithCovarianceStamped()

    checkpoint.header.frame_id = "/map"

    checkpoint.pose.pose.position.x = 0.0
    checkpoint.pose.pose.position.y = -7.0
    checkpoint.pose.pose.position.z = 0.0

    [x,y,z,w]=quaternion_from_euler(0.0,0.0,0.0)
    checkpoint.pose.pose.orientation.x = x
    checkpoint.pose.pose.orientation.y = y
    checkpoint.pose.pose.orientation.z = z
    checkpoint.pose.pose.orientation.w = w

    pub.publish(checkpoint)

if __name__ == '__main__':
    try:
        pub_init_pose()
    except rospy.ROSInterruptException:
        pass