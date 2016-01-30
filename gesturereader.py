import myo as libmyo

#Defauts
USE_ORIENTATION = True
USE_POSe = True
USE_GYROSCOPE = False
USE_ACCELEROMETER = False
USE_EEG = False

# Long term should probably make a lot of these private
class GestureListener(libmyo.DeviceListener):

    # run
    def __init__(self, run_rate, geture_time_cutoff=40, geture_distance_cutoff=30, use_orientation=USE_ORIENTATION, use_gyroscope=USE_GYROSCOPE, use_accelerometer=USE_ACCELEROMETER, use_emg=USE_EEG, use_pose=USE_POSE):
        super(GestureListener, self).__init__()
        self.run_rate = run_rate

        self.use_emg = use_emg
        self.use_gyroscope = use_gyroscope
        self.use_accelerometer = use_accelerometer
        self.use_orientation = use_orientation

        self.at_rest = True
        self.gesturing = False
        self.last_movements_buffer = []
        self.at_rest_buffer = []
        self.gesture_data_buffer = []
        self.gesture_buffer

        self.orientaion
        self.pose
        self.accelerometer
        self.gyroscope
        self.emg

        self.time_cutoff = geture_time_cutoff
        self.distance_cutoff = geture_distance_cutoff

    #TODOin exceeds thresholds, clear last_movements buffer everyonce in a while
    #TODO when writing back to use, flatten gesture data to simple array

    def on_orientation_data(self, myo, timestamp, quat):
        if self.use_orientation:
            V("Orientation data changed.")
            self.orientation = orientation

            # shared functionality
            state = self.__get_state()
            self.last_movements_buffer.append(state)

            if self.gesturing:
                self.gesture_data_buffer.append(state)

            self.at_rest = self.__is_at_rest()
            self.at_rest_buffer.append(self.at_rest)

            self.__check_thresholds_for_gesturing()
            if self.gesturing:
                self.gesture_data_buffer.append(state)

    def on_pose(self, myo, timestamp, post):
        if self.use_pose:
            V("Pose has changed", True)
            self.pose = pose
            self.last_movements_buffer.append(self.__get_state())

    def on_accelerometer_data(self, myo, timestamp, acceleration):
        if self.use_accelerometer:
            V("Accleration has changed")
            self.acceleration = acceleration
            self.last_movements_buffer.append(self.__get_state())

    def on_gyroscope_data(self, myo, timestamp, gyroscope):
        if self.use_gyroscope:
            V("Gyroscope has changed")
            self.gyroscope = gyroscope
            self.last_movements_buffer.append(self.__get_state())

    def on_emg_data(self, myo, timestamp, emg):
        if self.use_emg:
            V("Emg data has changed")
            self.emg = emg
            self.last_movements_buffer.append(self.__get_state())

    def __check_thresholds_for_gesturing(self):
        # clear last_movements_buffer if big periodically
        if len(self.last_movements_buffer) > self.time_cutoff*10:
            self.last_movements_buffer = self.last_movements_buffer[:self.time_cutoff]
            self.at_rest_buffer = self.at_rest_buffer[:self.time_cutoff]

        # Get the data up to the time threshold
        latestMovement = self.last_movements_buffer[:self.time_cutoff]

        latestRest = self.at_rest_buffer[:self.time_cutoff]

        # if we've been at rest for time threshold...
        if self.at_rest_buffer.count(self.at_rest_buffer) == len(self.at_rest_buffer):
            # if we were gesturing before, store the gesture and reset
            if self.gesturing:
                self.gesture_buffer.append(self.gesture_data_buffer)
                self.gesture_data_buffer = []
                self.gesturing = False
        # ... otherwise we are not officially at rest
        else:
            # if we were not gesturing
            if not self.gesturing:
                




    def __get_state(self):
        state = []
        if self.use_orientation:
            state.append(self.orientation)
        if self.use_pose:
            state.append(self.pose)
        if self.use_accelerometer:
            state.append(self.acceleration)
        if self.use_gyroscope:
            state.append(self.gyroscope)
        if self.use_emg:
            state.append(self.emg)
        return state


#TODO Disable locking??
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


        

class GestureReader(object):
    """
    An object for chuncking and reading gestures from the myo armband.
    Ideally, this would run in a thread. Instead, to get useful results,
    call the readGesture method repeatedly, and the class will chuck gestures
    for you. If you call it slowly, it won't do very much for you...

    Takes optional parameters
        myoPath -> a string pointing to the myo SDK
        geture_time_cutoff -> an integer representing the time required to divide 
            gestures by stillness in units of .05 seconds. Defaults to 40 (2 seconds)
        geture_distance_cutoff -> an integer representing the maximum distance that
            constitutes a new gesture in terms of squared unit myo quarternions # TODO calibrate

    """
    def __init__(self, myoPath=None, geture_time_cutoff=40, geture_distance_cutoff=30):
        super(GestureReader, self).__init__()
        libmyo.init(myoPath if myoPath is not None else DEFAULT_MYO_PATH)
        self.gestureBuffer = []
        self.listener = libmyo.DeviceListener(run_rate)

    def __enter__(self):
        self.hub = libmyo.Hub()
        self.hub.set_locking_policy(libmyo.LockPolicy.none)

    def __exit__(self, type, value, traceback):
        self.hub.shutdown()

    def readGesture(self):
        hub.run(1000/20, self.listener) # 20 times per second (1000 ms)