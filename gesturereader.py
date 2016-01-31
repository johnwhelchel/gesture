import myopython.myo as libmyo
import os

from scipy.spatial import distance
from queue import Queue
from math import pi
from functools import reduce

#Defauts
USE_ORIENTATION = True
USE_POSE = False
USE_GYROSCOPE = False
USE_ACCELEROMETER = True
USE_EMG = True

BASE_DIR = os.getcwd()
DEFAULT_MYO_PATH = os.path.join(BASE_DIR, "sdk/myo.framework")

VERBOSE = False

def V(text, override = False):
    if VERBOSE or override:
        print(text + '\n') 


def flatten(list):
    if list:
        return list if type(list) is not list else [item for sublist in list for item in sublist]
    return None

# Long term should probably make a lot of these private
class GestureListener(libmyo.DeviceListener):

    # run
    #TODO pick smart defaults
    def __init__(self, gesture_time_cutoff=40, emg_cutoff=60, gyro_cutoff=30, accel_cutoff=0.05, orient_cutoff=.1, use_orientation=USE_ORIENTATION, use_gyroscope=USE_GYROSCOPE, use_accelerometer=USE_ACCELEROMETER, use_emg=USE_EMG, use_pose=USE_POSE):
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
        self.acceleration = None
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
        myo.set_stream_emg(libmyo.StreamEmg.enabled)
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
            V("Pose has changed from " + str(self.pose) + " to " + str(pose))
            self.pose = pose
            self.handle_state_change()

    # ALWAYS USE FOR DISTANCE FUNCTION SO ALWAYS PERSIST
    def on_accelerometor_data(self, myo, timestamp, acceleration):
        V("Accleration has changed")
        self.acceleration = [acceleration.x, acceleration.y, acceleration.z]
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
        self.__check_thresholds_for_gesturing()

    def __clear_big_data_buffers(self):
        # clear last_movements_buffer if big periodically
        if len(self.last_movements_buffer) > self.time_cutoff*10:
            self.last_movements_buffer = self.last_movements_buffer[-self.time_cutoff:]
            self.at_rest_buffer = self.at_rest_buffer[-self.time_cutoff:]

    def __check_thresholds_for_gesturing(self):

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
                print("Beginning a gesture")




    def __get_state(self):
        return State(self.pose, self.emg, self.orientation, self.acceleration, self.gyroscope)

    #TODO Make this smarter
    def __get_at_rest(self):

        if len(self.last_movements_buffer) < 2: #Very first data read
            return True
            
        state_t = self.last_movements_buffer[-1:][0]
        state_t_minus_1 = self.last_movements_buffer[-2:-1][0]

        # New way, just accelerometer
        if state_t.acceleration is None or state_t_minus_1.acceleration is None:
            return True
        d = distance.euclidean(state_t.acceleration, state_t_minus_1.acceleration)
        return self.accel_cutoff > d

        # NB MUST BE SAME ORDER AS GET_STATE
        # pose is always first, so if that changes we've officially moved
        # if self.use_pose and state_t.pose != state_t_minus_1.pose:
        #     return False
        
        # return whatever is next in order
        # cutoff = None
        # if self.use_emg and state_t.emg is not None and state_t_minus_1.emg is not None:
        #     d = distance.euclidean(state_t.emg, state_t_minus_1.emg)
        #     #print(state_t.emg)
        #     #print(d)
        #     return self.emg_cutoff > d
        # elif self.use_orientation and state_t.orientation is not None and state_t_minus_1.orientation is not None:
        #     return self.orient_cutoff > distance.euclidean(state_t.orientation, state_t_minus_1.orientation)
        # elif self.use_accelerometer and state_t.acceleration is not None and state_t_minus_1.acceleration is not None:
        #     return self.accel_cutoff > distance.euclidean(state_t.acceleration, state_t_minus_1.acceleration)
        # else:
        #     return self.gyro_cutoff > distance.euclidean(state_t.gyroscope, state_t_minus_1.gyroscope)



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

    # TODO better spring handling here for items ala orientation
    def __str__(self):
        emg = str(self.emg)[1:-1].replace(" ", "") if self.emg is not None else "None"
        orientation = str(self.orientation)[1:-1].replace(" ", "") if self.orientation is not None else "None"
        acceleration = str(self.acceleration)[1:-1].replace(" ", "") if self.acceleration is not None else "None"
        gyroscope = str(self.gyroscope)[1:-1].replace(" ", "") if self.gyroscope is not None else "None"

        return str(self.pose.value) + "," + emg + "," + orientation + "," + acceleration + "," + gyroscope

    def __repr__(self):
        return self.__str__()
        

class GestureData(object):
    """docstring for GestureData"""
    def __init__(self, data):
        super(GestureData, self).__init__()
        self.all_data = data
        self.hand_data = GestureData.__create_hand_data(data)
        self.arm_data = GestureData.__create_arm_data(data)

    def as_classification_list(self):
        string = ""
        for state in self.all_data:
            string += str(state) + "\n"
        return [string]

    def __create_hand_data(all_data):
        return all_data #TODO

    def __create_arm_data(all_data):
        return all_data #TODO
        

        

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
            if self.listener.has_gesture():
                return GestureData(self.listener.get_gesture())


WORD = 'father_closed_emg'

if __name__ == '__main__':
    counter = 0
    fileName = WORD + str(counter)
    BASE_DIR = os.getcwd()
    filename = "/my/directory/filename.txt"
    os.makedirs(BASE_DIR +'/training/' + NAME)
    os.chdir(BASE_DIR + '/training/' +  NAME)
    file = open(fileName, '+w')
    with GestureReader() as gestureReader:
        while(True):
            print("in loop " + "\n")
            gestureData = gestureReader.readGesture()
            if (gestureData):
                data = ""
                for d in gestureData.all_data:
                    print(d)
                    data += str(d) + "\n"
                file.write(data)
                file.close()
                counter+=1
                fileName = WORD + str(counter)
                file = open(fileName, '+w')

