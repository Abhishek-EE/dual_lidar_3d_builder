import math
import numpy as np


# creates object for return-values of *CalcLidarData* function
class oldLidarData:
    def __init__(self, FSA, LSA, CS, Speed, TimeStamp, Confidence_i, Angle_i, Distance_i, offset_angle=0):
        self.FSA = FSA
        self.LSA = LSA
        self.CS = CS
        self.Speed = Speed
        self.TimeStamp = TimeStamp

        self.Confidence_i = Confidence_i
        self.Angle_i = Angle_i
        self.Distance_i = Distance_i

        x, y = polar2cartesian(self.Angle_i, self.Distance_i, offset_angle=offset_angle)
        self.x = x
        self.y = y
        
        
class LidarData:
    def __init__(self,FSA,LSA,CS,Speed,TimeStamp,Confidence_i,Angle_i,Distance_i, angDg_i):
        self.FSA = FSA
        self.LSA = LSA
        self.CS = CS
        self.Speed = Speed
        self.TimeStamp = TimeStamp

        self.Confidence_i = Confidence_i
        self.Angle_i = Angle_i
        self.Distance_i = Distance_i
        self.angDg_i = angDg_i


# https://stackoverflow.com/questions/20924085/python-conversion-between-coordinates
def polar2cartesian(angle, distance, offset_angle=0):
    angle = list(np.array(angle) + offset_angle)
    x = distance * -np.cos(angle)
    y = distance * np.sin(angle)
    return x, y
# def cartesian2polar(x, y):
#     distance = np.sqrt(x**2 + y**2)
#     angle = np.arctan2(y, x)
#     return angle, distance

def CalcLidarData(str):
    str = str.replace(' ','')

    Speed = int(str[2:4]+str[0:2],16)/100
    FSA = float(int(str[6:8]+str[4:6],16))/100
    LSA = float(int(str[-8:-6]+str[-10:-8],16))/100
    TimeStamp = int(str[-4:-2]+str[-6:-4],16)
    CS = int(str[-2:],16)

    Confidence_i = list()
    Angle_i = list()
    Distance_i = list()
    angDg_i = list()
    count = 0
#    if(LSA-FSA > 0):
#        angleStep = float(LSA-FSA)/(12)
#    else:
#        angleStep = float((LSA+360)-FSA)/(12)
    if(LSA-FSA > 0):
        angleStep = float(LSA-FSA)/(12)
    else:
        angleStep = float((LSA+360)-FSA)/(12)
    
    counter = 0
    circle = lambda deg : deg - 360 if deg >= 360 else deg
    for i in range(0,6*12,6): 
        Distance_i.append(int(str[8+i+2:8+i+4] + str[8+i:8+i+2],16)/10)
        Confidence_i.append(int(str[8+i+4:8+i+6],16))
        Angle_i.append(circle(angleStep*counter+FSA)*math.pi/180.0)
        angDg_i.append(math.degrees(circle(angleStep*counter+FSA)*math.pi/180.0))
        counter += 1
    

    lidarData = LidarData(FSA,LSA,CS,Speed,TimeStamp,Confidence_i,Angle_i,Distance_i, angDg_i)
    return lidarData


#=======================
def plot_3D(pointcloud):
    xs = pointcloud[:, 0]
    ys = pointcloud[:, 1]
    zs = pointcloud[:, 2]
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(projection='3d')
    ax.set_box_aspect((np.ptp(xs), np.ptp(ys), np.ptp(zs)))
    img = ax.scatter(xs, ys, zs, s=1)  # , c=t_low, cmap=plt.hot())
    fig.colorbar(img)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    plt.show()


#=======================
def rotate3d(points3d, rotation_axis, rotation_degrees):
    # define 3D rotation
    rotation_radians = np.radians(rotation_degrees)
    rotation_vector = rotation_radians * rotation_axis
    rotation = Rotation.from_rotvec(rotation_vector)

    # apply rotation to each point
    result_points = points3d.copy()
    for i, point in enumerate(points3d):
        result_points[i] = rotation.apply(point)

    return result_points


# 3D rotation about up-axis (Z)
rotation_axis = np.array([0, 0, 1])
angular_resolution = 1  # in degrees


#========================
def from_matrix_to_pose_dict(matrix):
    pose = {}
    # From http://steamcommunity.com/app/358720/discussions/0/358417008714224220/#c359543542244499836
    position = {}
    position['x'] = matrix[0][3]
    position['y'] = matrix[1][3]
    position['z'] = matrix[2][3]
    q = {}
    q['w'] = math.sqrt(max(0, 1 + matrix[0][0] + matrix[1][1] + matrix[2][2])) / 2.0
    q['x'] = math.sqrt(max(0, 1 + matrix[0][0] - matrix[1][1] - matrix[2][2])) / 2.0
    q['y'] = math.sqrt(max(0, 1 - matrix[0][0] + matrix[1][1] - matrix[2][2])) / 2.0
    q['z'] = math.sqrt(max(0, 1 - matrix[0][0] - matrix[1][1] + matrix[2][2])) / 2.0
    q['x'] = math.copysign(q['x'], matrix[2][1] - matrix[1][2])
    q['y'] = math.copysign(q['y'], matrix[0][2] - matrix[2][0])
    q['z'] = math.copysign(q['z'], matrix[1][0] - matrix[0][1])
    pose['position'] = position
    pose['orientation'] = q
    return pose


#Ported from https://www.reddit.com/r/Vive/comments/6toiem/how_to_get_each_axis_rotation_from_vive/dlmczdn/
def NormalizeAngle(angle):
    while (angle > 360):
        angle -= 360
    while (angle < 0):
        angle += 360
    return angle

def NormalizeAngles(angles):
    angles['x'] = NormalizeAngle(angles['x'])
    angles['y'] = NormalizeAngle(angles['y'])
    angles['z'] = NormalizeAngle(angles['z'])
    return angles

def RadianToDegree(angles):
    angles['x'] = math.degrees(angles['x'])
    angles['y'] = math.degrees(angles['y'])
    angles['z'] = math.degrees(angles['z'])
    return angles

def get_proper_euler(matrix):
    in_quat = from_matrix_to_pose_dict(matrix)
    sqw = in_quat['orientation']['w'] * in_quat['orientation']['w']
    sqx = in_quat['orientation']['x'] * in_quat['orientation']['x']
    sqy = in_quat['orientation']['y'] * in_quat['orientation']['y']
    sqz = in_quat['orientation']['z'] * in_quat['orientation']['z']
    unit = sqx + sqy + sqz + sqw # if normalised is one, otherwise is correction factor
    test = in_quat['orientation']['x'] * in_quat['orientation']['w'] - in_quat['orientation']['y'] * in_quat['orientation']['z']

    v = { 'x': 0, 'y': 0, 'z':0 }

    if (test > 0.49995 * unit): #singularity at north pole
        v['y'] = 2.0 * math.atan2(in_quat['orientation']['y'], in_quat['orientation']['x'])
        v['x'] = math.pi / 2.0
        v['z'] = 0
        return NormalizeAngles(RadianToDegree(v))

    if (test > 0.49995 * unit): #singularity at south pole
        v['y'] = -2.0 * math.atan2(in_quat['orientation']['y'], in_quat['orientation']['x'])
        v['x'] = -math.pi / 2.0
        v['z'] = 0
        return NormalizeAngles(RadianToDegree(v))

    v['y'] = math.atan2(2 * in_quat['orientation']['x'] * in_quat['orientation']['w'] + 2.0 * in_quat['orientation']['y'] * in_quat['orientation']['z'], 1 - 2.0 * (in_quat['orientation']['z'] * in_quat['orientation']['z'] + in_quat['orientation']['w'] * in_quat['orientation']['w'])) # Yaw
    v['x'] = math.asin(2 * (in_quat['orientation']['x'] * in_quat['orientation']['z'] - in_quat['orientation']['w'] * in_quat['orientation']['y'])) # Pitch
    v['z'] = math.atan2(2 * in_quat['orientation']['x'] * in_quat['orientation']['y'] + 2.0 * in_quat['orientation']['z'] * in_quat['orientation']['w'], 1 - 2.0 * (in_quat['orientation']['y'] * in_quat['orientation']['y'] + in_quat['orientation']['z'] * in_quat['orientation']['z'])) # Roll
    return NormalizeAngles(RadianToDegree(v))

def convert_to_euler(pose_mat):
    x = pose_mat[0][3]
    y = pose_mat[1][3]
    z = pose_mat[2][3]
    rot = get_proper_euler(pose_mat)
    return [x,y,z,rot['x'],rot['y']-180,rot['z']] #Y is flipped!


