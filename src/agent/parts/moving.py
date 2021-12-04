import os
import time
import rospy

from time import time
from navigation.provide_goal_pose import MAX_TIME, pub_goal_pose
from actionlib_msgs.msg import GoalStatus, GoalStatusArray
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped, Twist
from move_base_msgs.msg import MoveBaseAction
from actionlib import SimpleActionClient
from utils.geom import make_pose_cov, make_pose, is_near


class Moving():
    MAX_TIME_FOR_NAVIGATION = 60.0  # Seconds
    LINEAR_VEL = 0.5
    ANGULAR_VEL = 2.0
    VEL_PUB_DURATION_LINEAR = 0.5  # Seconds
    VEL_PUB_DURATION_ANGULAR = 2.0  # Seconds

    def __init__(self):
        self.mname = "[ROBOTCORE] "
        self.initial_pose = make_pose_cov(0, -7)
        self.current_pose = make_pose_cov(0, -7)
        self.status = None
        self.recovery_counter = 0

        self.pose_publisher = rospy.Publisher(
            "/initialpose", PoseWithCovarianceStamped, queue_size=10)
        self.goal_publisher = rospy.Publisher(
            "/move_base_simple/goal", PoseStamped, queue_size=10)
        self.status_subscriber = rospy.Subscriber(
            "/move_base/status", GoalStatusArray, self.status_callback, queue_size=1)
        self.amcl_subscriber = rospy.Subscriber(
            "/amcl_pose", PoseWithCovarianceStamped, self.robot_pose_callback, queue_size=10)

        rospy.sleep(5)


    def init_pose(self):
        # Set the initial pose of the robot
        self.pose_publisher.publish(self.initial_pose)

    def status_callback(self, status):
        self.status = status

    def robot_pose_callback(self, pose):
        self.current_pose = make_pose(
            pose.pose.pose.position.x, pose.pose.pose.position.y)

    def get_status(self):
        if self.status != None and len(self.status.status_list) > 0:
            return int(self.status.status_list[-1].status)

        return GoalStatus.ABORTED

    def cancel_path(self):
        """ Cancels the current path
        """
        client = SimpleActionClient('move_base', MoveBaseAction)
        client.wait_for_server()
        client.cancel_all_goals()
        rospy.loginfo("Cancelled goal_pose")

    def _move_lin(self, lin):
        """ Moves linearly
        Args:
            lin (float): the linear velocity
        """
        pub_velocity = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
        twist = Twist()

        twist.linear.x = lin

        # Connect with the publisher
        while pub_velocity.get_num_connections() < 1:
            pass

        init_time = time()
        duration = 0
        # Publish to the /cmd_vel topic
        while duration < self.VEL_PUB_DURATION_LINEAR:
            pub_velocity.publish(twist)
            duration = time() - init_time
        rospy.loginfo("Moved Linearly")

    def _move_ang(self, ang):
        """ Moves angularly
        Args:
            ang (float): the angular velocity
        """
        pub_velocity = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
        twist = Twist()

        twist.angular.z = ang

        # Connect with the publisher
        while pub_velocity.get_num_connections() < 1:
            pass

        init_time = time()
        duration = 0
        # Publish to the /cmd_vel topic
        while duration < self.VEL_PUB_DURATION_ANGULAR:
            pub_velocity.publish(twist)
            duration = time() - init_time
        rospy.loginfo("Turned")

    def move_forward(self):
        self._move_lin(self.LINEAR_VEL)

    def move_backward(self):
        self._move_lin(-self.LINEAR_VEL)

    def turn_left(self):
        self._move_ang(self.ANGULAR_VEL)

    def turn_right(self):
        self._move_ang(-self.ANGULAR_VEL)

    def recovery(self, pose):
        """ Cancels the current path, then moves around to get unstuck
        and then calls pub_goal_pose again to the same path
        Args:
            pose (): goal pose
        """
        rospy.loginfo("Recovery Started")
        self.recovery_counter += 1
        self.cancel_path()

        self.move_forward()
        self.turn_right()
        self.move_forward()
        self.turn_left()

        rospy.loginfo("Recovery Ended")
        rospy.loginfo("Trying again")
        # pub_goal_pose(x, y, theta)
        self.goto_pose(pose)

    def goto_pose(self, pose):

        def clear_costmaps():
            rospy.loginfo("Clearing Costmaps")
            os.system('rosservice call /move_base/clear_costmaps \"{}\"')
            rospy.sleep(0.5)
            # self.goal_publisher.publish(pose)

        if self.recovery_counter > 2:
            rospy.logerr(self.mname + "Could not get to location")
            return

        print(self.mname + "Departure - publishing to NavStack")
        clear_costmaps()
        self.goal_publisher.publish(pose)
        rospy.sleep(2)
        order_status = self.get_status()

        counter = 0
        init_time = time()
        time_passed = 0
        while order_status != GoalStatus.SUCCEEDED:

            # d, r, b = is_near(self.current_pose, pose, radius=1.5)
            # print(d, r)

            if order_status == GoalStatus.ABORTED:
                print(self.mname + "Unreachable location. Retrying.")
                clear_costmaps()
                self.recovery(pose)
            elif order_status != GoalStatus.ACTIVE:
                print(f"Order status: {order_status}")

            counter += 1

            if counter == 20:
                counter = 0
                clear_costmaps()

            rospy.sleep(0.2)
            order_status = self.get_status()

            time_passed = time() - init_time
            if time_passed > MAX_TIME:
                self.recovery(pose)

            # if b:
            #     # If near target position, publish self pose so it's automatically successful
            #     # self.goal_publisher.publish(self.current_pose)
            #     self.cancel_path()

        print(self.mname + "Arrival")

    def move_to(self, target_pos):
        pub_goal_pose(target_pos.position.x, target_pos.position.y, 0)

    def turn_to(self, target_pos):
        pass
