#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import math
import yaml
import roslaunch
import rospy
import rospkg
import numpy as np
import csv
import pickle
from geometry_msgs.msg import Twist, Point, Pose, PoseStamped
from nav_msgs.msg import Odometry, OccupancyGrid
from std_msgs.msg import Float32, Bool
import scipy
from scipy.optimize import fmin, minimize
from transforms3d.quaternions import mat2quat, quat2mat




def T_to_pose(T):

    pose = Pose()
    pose.position.x = T[0][3]
    pose.position.y = T[1][3]
    pose.position.z = T[2][3]
    
    R = T[:3, :3]
    quat = mat2quat(R)
    pose.orientation.x = quat[1]
    pose.orientation.y = quat[2]
    pose.orientation.z = quat[3]
    pose.orientation.w = quat[0]
    
    return pose

def pose_to_T2(pose):
    
    q1 = pose.orientation.x
    q2 = pose.orientation.y
    q3 = pose.orientation.z
    q4 = pose.orientation.w
    x = pose.position.x
    y = pose.position.y
    z = pose.position.z
    R = quat2mat([q4, q1, q2, q3])
    
    T = np.zeros([4, 4])
    T[:3, :3] = R
    T[0, 3] = x
    T[1, 3] = y
    T[2, 3] = z
    T[3, 3] = 1
    return T

    
def pose_to_T(poseStamp: PoseStamped):

    pose = poseStamp.pose
    q1 = pose.orientation.x
    q2 = pose.orientation.y
    q3 = pose.orientation.z
    q4 = pose.orientation.w
    x = pose.position.x
    y = pose.position.y
    z = pose.position.z
    R = quat2mat([q4, q1, q2, q3])
    
    T = np.zeros([4, 4])
    T[:3, :3] = R
    T[0, 3] = x
    T[1, 3] = y
    T[2, 3] = z
    T[3, 3] = 1
    return T


def select_points(T0A):
    tol = 0.005
    T_good = []
    for i in range(len(T0A)):
        if i == 0:
            T_good.append(T0A[i])
        else:
            xi = T0A[i].pose.position.x
            yi = T0A[i].pose.position.y
            zi = T0A[i].pose.position.z
            for j in T_good:
                N = len(T_good)
                k = 0
                xj = j.pose.position.x
                yj = j.pose.position.y
                zj = j.pose.position.z
                
                if math.sqrt((xi-xj)**2 + (yi-yj)**2 + (zi-zj)**2) > tol:
                    k += 1
            if k == N: 
                T_good.append(T0A[i])
    return T_good
                

def objectiveFunPosition(p, R, T_data):
    """
    Optimization for position
    """
    T0A = T_data.copy()
    with open('/home/developer/catkin_ws/src/for_franka_ros/data/tf_calib.pickle', 'wb') as f:
    # Pickle the 'data' dictionary using the highest protocol available.
        pickle.dump(T0A, f, pickle.HIGHEST_PROTOCOL)
    f.close()
    
    #T0A = select_points(T0A)
    # Initial supposed transform
    Tx = np.eye(4)
    Tx[:3, :3] = R
    Tx[:3, 3] = p

    num_of_mesurs = len(T0A)  # holds the number of measurements
    f = 0  # optimization function value initialized to 0
    for i in range(0, num_of_mesurs):
        T_OI = np.matmul(T0A[i], Tx) 
        for j in range(0, num_of_mesurs):
            T_OJ = np.matmul(T0A[j], Tx) 
            p_ = T_OI[:3, 3] - T_OJ[:3, 3]
            f += np.linalg.norm(p_)  # Euclidean distance
    print(f)
    return f

def f_optimizePointOrientation(T_init, callibration_data_poses):

    
    R1 = T_init[:3, :3]  # Initial rotation matrix
    P1 = T_init[:3, 3]   # Initial position vector

    # Optimize position using fmin
    P1_optimized = fmin(func=objectiveFunPosition, x0=np.array([0,0,-0.12]), args=(R1, callibration_data_poses), xtol=1e-10, ftol=1e-10,  disp=True)

    print("optimization finished")
    print(P1_optimized)
    T = np.eye(4)
    T[:3, 3] = P1_optimized

    return T

def CalculateCalipenTransformation(callibration_data_poses):
        T_init = np.eye(4, 4)
        T_init[2,3] = -0.12
        print(T_init)
        T = f_optimizePointOrientation(T_init, callibration_data_poses)
        return T

