import math
from numpy import random as np_random

class Event:
    def __init__(self, identifier, event_type, curr_system, target_system, time):
        self.identifier    = identifier         # event id
        self.type          = event_type         # "arrival" or "departure"
        self.curr_system   = curr_system        # current system: "general" or "specific"
        self.target_system = target_system      # "general" or "specific"
        self.time          = time               # time of event

    def __str__(self):

        return f"ID: {self.identifier},\tEvent type: {self.type},\tCurrent system: {self.curr_system},  \tTarget system: {self.target_system},  \tTime: {round(self.time, 2)}"
        
    def get_duration(self):

        s = 0
        if self.target_system == "general":
            while s < 60:
                s = - math.log(np_random.random()) * 120           # - 2min * ln(u) ; u ~ U(0,1) ; [60, +inf]

        elif self.target_system == "specific" and self.curr_system == "general":
            while s < 30 or s > 120:
                s = np_random.normal(60, 20)                         # N(60, 20)  [30, 120]

        else:
            while s < 60:
                s = - math.log(np_random.random()) * 150            # - 2.5min * ln(u) ; u ~ U(0,1) [60, + inf]

        return s

class System:

    def __init__(self, max_resources, queue_length, system_type):
        self.max_resources = max_resources          # number of maximum resources
        self.queue_length  = queue_length           # length of the waiting queue
        self.system_type   = system_type            # "general" or "specific"

        self.time_intervals = []                    # list of time intervals between arrivals
        self.general_time_intervals  = []           # list of time intervals between general event arrivals (empty for specific system)
        self.specific_time_intervals = []           # list of time intervals between specific event arrivals
        self.waiting_time_intervals  = []           # list of time intervals between arrival and service
        self.waiting_queue  = []                    # list of delayed calls
        self.avg_waiting    = []                    # average waiting time predictions
        self.received_calls = 0                     # number of received calls
        self.active_calls   = 0                     # number of active calls
        self.delayed_calls  = 0                     # number of delayed calls                         
        self.rejected_calls = 0                     # number of rejected calls

    def store_interval(self, event, s):
        if event.target_system == "general":
                self.general_time_intervals.append(s)
        else:
            self.specific_time_intervals.append(s)

    def arrival(self, event, event_timeline):

        self.received_calls += 1
        
        if self.active_calls <= self.max_resources:             # check if there are resources available
            
            self.active_calls += 1                              # update number of active calls
            s = event.get_duration()                            # get duration of call based on event properties
            self.store_interval(event, s)
            
            next_departure = event.time + s                     # generate next departure time
    
            event_timeline.append(Event(event.identifier, "departure", self.system_type, event.target_system, next_departure))

        else: # Call is delayed or blocked
            if (self.queue_length > 0 and len(self.waiting_queue) < self.queue_length) or self.queue_length == -1:
                self.delayed_calls += 1
                self.waiting_queue.append(event)
                
                if self.system_type == "general":                       # Predict waiting time
                    dmed = 0.3*60 + 0.7*120                             # Average service time
                    pred_time = len(self.waiting_queue)*dmed            # dmed * number of calls in queue
                    self.avg_waiting.append(pred_time)

            else:
                self.rejected_calls += 1                            # update number of rejected calls  

            return None              

    def departure(self, event, event_timeline):
            
        if self.active_calls > 0:
            self.active_calls -= 1

        if self.system_type == "general" and event.target_system == "specific":  # generate arrival for specific system
            
            event_timeline.append(Event(event.identifier, "arrival", "specific", event.target_system, event.time))

        #print(self.waiting_queue)
        if len(self.waiting_queue) > 0:                                         # check if there are waiting calls

            waiting_call = self.waiting_queue.pop(0)                            # pop first call from waiting calls
            self.waiting_time_intervals.append(event.time - waiting_call.time)  # store waiting time

            self.arrival(waiting_call, event_timeline)
        
    def get_metrics(self):

        prob_delay = self.delayed_calls  / self.received_calls
        prob_block = self.rejected_calls / self.received_calls

        avg_delay        = sum(self.waiting_time_intervals) / self.received_calls
        avg_waiting_time = sum(self.waiting_time_intervals) / len(self.waiting_time_intervals) if len(self.waiting_time_intervals) > 0 else 0
        
        avg_general_service_time  = sum(self.general_time_intervals) / len(self.general_time_intervals) if len(self.general_time_intervals) > 0 else 0
        avg_specific_service_time = sum(self.specific_time_intervals) / len(self.specific_time_intervals)

        predicton_error = []

        i = len(self.waiting_time_intervals)
        j = len(self.avg_waiting)
        rng = i if i < j else j

        for i in range(rng):
            predicton_error.append(round(abs(self.waiting_time_intervals[i] - self.avg_waiting[i]), 5))

        return prob_delay, prob_block, avg_delay, avg_waiting_time, avg_general_service_time, avg_specific_service_time, predicton_error
        
