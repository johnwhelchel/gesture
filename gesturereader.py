import myopython.myo as libmyo
import os

from scipy.spatial import distance
from queue import Queue
from math import pi
from functools import reduce

#Defauts
USE_ORIENTATION = True
USE_POSE = True
USE_GYROSCOPE = False
USE_ACCELEROMETER = False
USE_EEG = False

BASE_DIR = os.getcwd()
DEFAULT_MYO_PATH = os.path.join(BASE_DIR, "sdk/myo.framework")

VERBOSE = False

def V(text, override = False):
    if VERBOSE or override:
        print(text + '\n') 

# Long term should probably make a lot of these private
class GestureListener(libmyo.DeviceListener):

    # run
    #TODO pick smart defaults
    def __init__(self, gesture_time_cutoff=40, emg_cutoff=10, gyro_cutoff=30, accel_cutoff=10, orient_cutoff=.1, use_orientation=USE_ORIENTATION, use_gyroscope=USE_GYROSCOPE, use_accelerometer=USE_ACCELEROMETER, use_emg=USE_EEG, use_pose=USE_POSE):
        super(GestureListener, self).__init__()

        self.use_emg = use_emg
        self.use_gyroscope = use_gyroscope
        self.use_accelerometer = use_accelerometer
        self.use_orientation = use_orientation
        self.use_pose = use_pose

        self.gesturing = False
        self.last_movements_buffer = []
        self.at_rest_buffer = []
        self.gesture_data_buffer = []
        self.gesture_buffer = Queue()

        self.orientation = None
        self.pose = libmyo.Pose.rest
        self.accelerometer = None
        self.gyroscope = None
        self.emg = None

        self.time_cutoff = gesture_time_cutoff
        self.emg_cutoff = emg_cutoff
        self.gyro_cutoff = gyro_cutoff
        self.accel_cutoff = accel_cutoff
        self.orient_cutoff = orient_cutoff

    def has_gesture(self):
        return not self.gesture_buffer.empty()

    def get_gesture(self):
        return self.gesture_buffer.get()

    def on_orientation_data(self, myo, timestamp, quat):
        if self.use_orientation:
            V("Orientation data changed.")
            self.orientation = list(quat.rpy)
            # normalize a la hello.cpp
            self.orientation[0] = ((self.orientation[0] + pi) / (2.0*pi)) * 18
            self.orientation[1] = ((self.orientation[1] + pi) / (2.0*pi)) * 18
            self.orientation[2] = ((self.orientation[2] + pi) / (2.0*pi)) * 18
            self.handle_state_change()

    def on_pose(self, myo, timestamp, pose):
        if self.use_pose:
            V("Pose has changed from " + str(self.pose) + " to " + str(pose), True)
            self.pose = pose
            self.handle_state_change()

    def on_accelerometer_data(self, myo, timestamp, acceleration):
        if self.use_accelerometer:
            V("Accleration has changed")
            self.acceleration = acceleration
            self.handle_state_change()

    def on_gyroscope_data(self, myo, timestamp, gyroscope):
        if self.use_gyroscope:
            V("Gyroscope has changed")
            self.gyroscope = gyroscope
            self.handle_state_change()

    def on_emg_data(self, myo, timestamp, emg):
        if self.use_emg:
            V("Emg data has changed")
            self.emg = emg
            self.handle_state_change()

    def handle_state_change(self):
        state = self.__get_state()
        self.last_movements_buffer.append(state)
        #print(self.__get_at_rest())
        self.at_rest_buffer.append(self.__get_at_rest())

        if self.gesturing:
            self.gesture_data_buffer.append(state)

        self.__clear_big_data_buffers()
        self.__check_thresholds_for_gesturing(state)

    def __clear_big_data_buffers(self):
        # clear last_movements_buffer if big periodically
        if len(self.last_movements_buffer) > self.time_cutoff*10:
            self.last_movements_buffer = self.last_movements_buffer[-self.time_cutoff:]
            self.at_rest_buffer = self.at_rest_buffer[-self.time_cutoff:]

    def __check_thresholds_for_gesturing(self, state):

        # Get the data up to the time threshold
        latest_rest = self.at_rest_buffer[-self.time_cutoff:]

        gesture_cut_off = latest_rest.count(latest_rest[0]) == len(latest_rest)

        # if we've been at rest for time threshold...
        if gesture_cut_off:
            # if we were gesturing before, store the gesture and reset
            if self.gesturing:
                self.gesture_buffer.put(self.gesture_data_buffer)
                self.gesture_data_buffer = []
                self.gesturing = False
                print("Gesture is over")
        # ... otherwise we are gesturing
        else:
            # if we were not gesturing, we now are
            if not self.gesturing:
                self.gesturing = True
                print("Begining a gesture")




    # NB MUST BE SAME ORDER AS AT_REST
    def __get_state(self):
        return State(self.pose.Value, self.emg, self.orientation, self.acceleration, self.gyroscope)
        if self.use_pose:
            state.append(self.pose)
        if self.use_emg:
            state.append(self.emg)
        if self.use_orientation:
            state.append(self.orientation)
        if self.use_accelerometer:
            state.append(self.acceleration)
        if self.use_gyroscope:
            state.append(self.gyroscope)
        return state

    #TODO Make this smarter
    def __get_at_rest(self):

        if len(self.last_movements_buffer) < 2: #Very first data read
            return True
            
        state_t = self.last_movements_buffer[-1:][0]
        state_t_minus_1 = self.last_movements_buffer[-2:-1][0]

        # NB MUST BE SAME ORDER AS GET_STATE
        # pose is always first, so if that changes we've officially moved
        if self.use_pose and state_t[0] != state_t_minus_1[0]:
            return False
        elif self.use_pose:
            state_t = state_t[1:]
            state_t_minus_1 = state_t_minus_1[1:]
        
        # return whatever is next in order
        cutoff = None
        if self.use_emg:
            cutoff = self.emg_cutoff
        elif self.use_orientation:
            cutoff = self.orient_cutoff
        elif self.use_accelerometer:
            #TODO define vectors
            cutoff = self.accel_cutoff
        else:
            #TODO define vectors
            cutoff = self.gyro_cutoff

        d = distance.euclidean(state_t, state_t_minus_1)
        #print(d)
        return cutoff > d



#region Not so important overrides
    def on_arm_sync(self, myo, timestamp, arm, x_direction, rotation, warmup_state):
        V("Myo has synced, dude " + str(timestamp))
        myo.vibrate("short")

    def on_arm_unsync(self, myo, timestamp):
        V("Myo is lost now " + str(timestamp))
        myo.vibrate("medium")

    def on_pair(self, myo, timestamp, firmware_version):
        V("Myo has paired, bitches. Time for some ASL at " + str(timestamp))

    def on_unpair(self, myo, timestamp):
        V("Myo says 'deuces' at " + str(timestamp))
#endregion

class State(object):
    """docstring for State"""
    def __init__(self, pose, emg, orientation, acceleration, gyroscope):
        super(State, self).__init__()
        self.pose = pose
        self.emg = emg
        self.orientation = orientation
        self.acceleration = acceleration
        self.gyroscope = gyroscope

    # def __str__(self):
        # return self.pose.Value + "," + self.emg + "," + self.orientation + "," self.acceleration + "," + self.gyroscope
        

# class GestureData(object):
#     """docstring for Gesture"""
#     def __init__(self, hand_data, arm_data):
#         super(Gesture, self).__init__()
#         self.hand_data = hand_data
#         self.arm_data = arm_data
        

        

class GestureReader(object):
    """
    An object for chunking and reading gestures from the myo armband.
    Ideally, this would run in a thread. Instead, to get useful results,
    call the readGesture method repeatedly, and the class will chuck gestures
    for you. If you call it slowly, it won't do very much for you...

    Takes optional parameters
        myoPath -> a string pointing to the myo SDK
        geture_time_cutoff -> an integer representing the time required to divide 
            gestures by stillness in units of .05 seconds. Defaults to 40 (2 seconds)
        geture_distance_cutoff -> an integer representing the maximum distance that
            constitutes a new gesture in terms of squared unit myo quarternions
    """
    def __init__(self, myoPath=None):
        super(GestureReader, self).__init__()
        libmyo.init(myoPath if myoPath is not None else DEFAULT_MYO_PATH)
        self.listener = GestureListener()

    def __enter__(self):
        self.hub = libmyo.Hub()
        self.hub.run(int(1000/20), self.listener) # 1000/20 = 50 i.e. 20 times per second (1000 ms)
        try:
            self.hub.set_locking_policy(libmyo.LockingPolicy.none)
        except:
            print("locking policy failed")
        return self

    def __exit__(self, type, value, traceback):
        self.hub.shutdown()

    def readGesture(self):
        while (True):
            stringGesture = ["test", "test2"]
            return stringGesture
            if self.listener.has_gesture():
                gest = self.listener.get_gesture()
                flattenedGesture = GestureReader.flatten(gest)

                gesture = [[int(item) for item in items] if type(items) is list else items for items in flattenedGesture]
                stringifiedGesture = [",".join(map(str, item)) if type(item) is list else item.name for item in gesture]
                # gestureData = 
                print(stringGesture)
                return stringGesture


    def flatten(list):
        return [item for sublist in list for item in sublist]

WORD = 'father'

if __name__ == '__main__':
    counter = 0
    fileName = WORD + str(counter)
    file = open(fileName, '+w')

    with GestureReader() as gestureReader:
        while(True):
            print("in loop " + "\n")
            gestureData = gestureReader.readGesture()
            if (gestureData):
                file.write(''.join(gestureData))
                file.close()
                counter+=1
                fileName = WORD + str(counter)
                file = open(fileName, '+w')

