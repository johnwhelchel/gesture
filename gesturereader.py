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
USE_ACCELEROMETER = False      
USE_EMG = False
USE_COUNT = True

BASE_DIR = os.getcwd()
DEFAULT_MYO_PATH = os.path.join(BASE_DIR, "sdk/myo.framework")

VERBOSE = False

NOWRITE = False

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
    def __init__(self, end_time_cutoff=40, begin_time_cutoff=5, emg_cutoff=60, gyro_cutoff=30, accel_cutoff=10, orient_cutoff=.1, use_count=USE_COUNT, use_orientation=USE_ORIENTATION, use_gyroscope=USE_GYROSCOPE, use_accelerometer=USE_ACCELEROMETER, use_emg=USE_EMG, use_pose=USE_POSE):
        super(GestureListener, self).__init__()

        self.count = 0

        self.use_count = use_count
        self.use_emg = use_emg
        self.use_gyroscope = use_gyroscope
        self.use_accelerometer = use_accelerometer
        self.use_orientation = use_orientation
        self.use_pose = use_pose

        self.gesturing = False
        self.last_movements_buffer = []
        self.at_rest_buffer = [True]
        self.gesture_data_buffer = []
        self.gesture_buffer = Queue()

        self.orientation = None
        self.pose = libmyo.Pose.rest
        self.acceleration = None
        self.gyroscope = None
        self.emg = None

        self.bad_accel_count = 0

        self.end_time_cutoff = end_time_cutoff
        self.begin_time_cutoff = begin_time_cutoff
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
        self.orientation = list(quat.rpy)
        # normalize a la hello.cpp
        self.orientation[0] = int((self.orientation[0] + pi) / (2.0*pi) * 100)
        self.orientation[1] = int((self.orientation[1] + pi) / (2.0*pi) * 100)
        self.orientation[2] = int((self.orientation[2] + pi) / (2.0*pi) * 100)
        if self.use_orientation:
            V("Orientation data changed.")
            self.handle_state_change()
            #self.__update_at_rest()


    def on_pose(self, myo, timestamp, pose):
        if self.use_pose:
            V("Pose has changed from " + str(self.pose) + " to " + str(pose))
            self.pose = pose
            self.handle_state_change()

    # ALWAYS USE FOR DISTANCE FUNCTION SO ALWAYS PERSIST
    def on_accelerometor_data(self, myo, timestamp, acceleration):
        V("Accleration has changed")
        self.acceleration = [acceleration.x*100, acceleration.y*100, acceleration.z*100]
        self.handle_state_change()
        self.__update_at_rest()

    def __update_at_rest(self):
        self.at_rest_buffer.append(self.__get_at_rest())


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

        if self.gesturing:
            self.gesture_data_buffer.append(state)

        self.__clear_big_data_buffers()
        self.__check_thresholds_for_gesturing()

    def __clear_big_data_buffers(self):
        # clear last_movements_buffer if big periodically
        if len(self.last_movements_buffer) > self.end_time_cutoff*10:
            self.last_movements_buffer = self.last_movements_buffer[-self.end_time_cutoff:]
            self.at_rest_buffer = self.at_rest_buffer[-self.end_time_cutoff:]

    def __check_thresholds_for_gesturing(self):

        # Get the data up to the time threshold
        gesture_end_latest_rest = self.at_rest_buffer[-self.end_time_cutoff:]
        gesture_begin_latest_rest = self.at_rest_buffer[-self.begin_time_cutoff:]

        gesture_cut_off = gesture_end_latest_rest.count(gesture_end_latest_rest[0]) == len(gesture_end_latest_rest)
        gesture_begin = gesture_begin_latest_rest[0] == False and gesture_begin_latest_rest.count(gesture_begin_latest_rest[0]) == len(gesture_begin_latest_rest)
        # if gesture_begin_latest_rest[0] == False:
        #     print('latest not at rest')
        #     print(gesture_begin_latest_rest)
        #     if gesture_begin_latest_rest.count(gesture_begin_latest_rest[0]) == len(gesture_begin_latest_rest):
        #         print("YEAH")

        # if we've been at rest for time threshold...
        if gesture_cut_off:
            # if we were gesturing before, store the gesture and reset
            if self.gesturing:
                self.gesture_buffer.put(self.gesture_data_buffer)
                self.gesture_data_buffer = []
                self.gesturing = False
                self.count = 0
                print("Gesture is over")
        # ... otherwise we may be gesturing anew
        elif gesture_begin:
            if not self.gesturing:
                self.gesturing = True
                print("Beginning a gesture")




    def __get_state(self):
        if self.gesturing:
            self.count+=1
        return State(self.pose, self.emg, self.orientation, self.acceleration, self.gyroscope, self.count)

    #TODO Make this smarter
    def __get_at_rest(self):

        if len(self.last_movements_buffer) < 2: #Very first data read
            return True

        if self.bad_accel_count < 200:
            if self.bad_accel_count is 10:
                print("Cleaning out bad acceleration data...")
            elif self.bad_accel_count is 199:
                print("Bad data cleaned! Waiting for a gesture.")
            self.bad_accel_count += 1
            return True
            
        state_t = self.last_movements_buffer[-1:][0]
        state_t_minus_1 = self.last_movements_buffer[-2:-1][0]

        # New way, just accelerometer
        if state_t.acceleration is None or state_t_minus_1.acceleration is None:
            return True
        d = distance.euclidean(state_t.acceleration, state_t_minus_1.acceleration) + distance.euclidean(state_t.orientation, state_t_minus_1.orientation)
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
    def __init__(self, pose, emg, orientation, acceleration, gyroscope, count):
        super(State, self).__init__()
        self.pose = pose
        self.emg = emg
        self.orientation = orientation
        self.acceleration = acceleration
        self.gyroscope = gyroscope
        self.count = count

    # TODO better spring handling here for items ala orientation
    def __str__(self):
        emg = str(self.emg)[1:-1].replace(" ", "") if self.emg is not None else "None"
        orientation = str(self.orientation)[1:-1].replace(" ", "") if self.orientation is not None else "None"
        acceleration = str(int(self.acceleration[0])) + "," + str(int(self.acceleration[1])) + "," + str(int(self.acceleration[2])) if self.acceleration is not None else "None"
        gyroscope = str(self.gyroscope)[1:-1].replace(" ", "") if self.gyroscope is not None else "None" 
        return str(self.pose.value) + "," + emg + "," + orientation + "," + acceleration + "," + gyroscope + "," + str(self.count)

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
        return string

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

WORD = 'mom'
NAME = 'FINALCOUNTDOWN'

if __name__ == '__main__':
    counter = 0
    filename = os.path.join(BASE_DIR, "training/" + NAME + "/" + WORD + str(counter))
    with GestureReader() as gestureReader:
        print("Word you are recording is " + WORD)
        while(True):
            print("Waiting for your next gesture... " + "\n")
            gestureData = gestureReader.readGesture()
            if (gestureData):
                data = ""
                for d in gestureData.all_data:
                    print(d)
                    data += str(d) + "\n"
                counter+=1
                if not NOWRITE:
                    with open(filename, '+w') as file:
                        file.write(data)
                    filename = os.path.join(BASE_DIR, "training/" + NAME + "/" + WORD + str(counter))

