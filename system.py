import math
import random
from matplotlib import pyplot
from numpy import random as np_random

class Event:
    def __init__(self, event_type, system, proccess_type, time):
        self.type = event_type            # "arrival" or "departure"
        self.proccess_type = proccess_type      # "general" or "specific"
        self.time = time
        self.system = system                    # current system "general" or "specific"

    def get_duration(self):

        if self.proccess_type == "general":
            s = 60 - math.log(random.uniform(0, 1)) * 120           # 1min - 2min * ln(u) ; u ~ U(0,1)
            if s > 300: s = 300

        elif self.proccess_type == "specific" and self.system == "general":
            s = np_random.normal(60, 20)                            # N(60, 20)  [30, 120]
            if   s > 120: s = 120
            elif s <  30: s = 30

        else:
            s = 60 - math.log(random.uniform(0, 1)) * 150           # 1min - 2.5min * ln(u) ; u ~ U(0,1)

        return s

class System:

    def __init__(self, max_resources, queue_length, system):
        self.max_resources = max_resources          # number of maximum resources
        self.queue_length  = queue_length           # length of the waiting queue
        self.system = system                        # "general" or "specific"

        self.time_intervals = []                    # list of time intervals between arrivals
        self.general_time_intervals = []            # list of time intervals between general arrivals
        self.specific_time_intervals = []           # list of time intervals between specific arrivals
        self.waiting_time_intervals = []            # list of time intervals between arrival and service
        self.waiting_queue  = []                    # list of delayed calls
        self.avg_waiting    = []                    # average waiting time predictions
        self.active_calls   = 0                     # number of active calls
        self.delayed_calls  = 0                     # number of delayed calls                         
        self.rejected_calls = 0                     # number of rejected calls

    def arrival(self, event):

        self.time_intervals.append(event.time)                  # store time interval
        self.active_calls += 1                                  # update number of active calls

        if self.active_calls <= self.max_resources:             # check if there are resources available
            s = event.get_duration()                            # get duration of call based on event properties
            next_departure = event.time + s                     # generate next departure time

            if event.proccess_type == "general":
                self.general_time_intervals.append(s)
            else:
                self.specific_time_intervals.append(s)

            return Event("departure", "general", event.proccess_type, next_departure)

        else:
            if (self.queue_length > 0 and len(self.waiting_queue) < self.queue_length) or self.queue_length == -1:
                self.delayed_calls += 1
                self.waiting_queue.append(event)                    # store delayed call
                n = len(self.waiting_time_intervals)
                if n > 0:
                    self.avg_waiting.append(sum(self.waiting_time_intervals)/n)   # store average waiting time prediction
                else:
                    self.avg_waiting.append(0)
            else:
                self.rejected_calls += 1                            # update number of rejected calls                

    def departure(self, event):
            
        if self.active_calls > 0:
            self.active_calls -= 1

        if len(self.waiting_queue) > 0:                                 # check if there are waiting calls

            arrival = self.waiting_queue.pop(0)                         # remove first call from delayed calls
            self.waiting_time_intervals.append(event.time - arrival.time)  # store delay
            self.active_calls += 1                                      # update number of active calls

            s = event.get_duration()                                    # get duration of call based on event properties
            next_departure = event.time + s                              # generate next departure time
            
            return Event("departure", self.system, event.proccess_type, next_departure)
        
        if self.system == "general" and event.proccess_type == "specific":  # generate arrival for specific system
            event.system = "specific"
            
            return Event("arrival", "specific", event.proccess_type, event.time)
        
    def get_metrics(self):

        predicton_error = []
        prob_delay = self.delayed_calls  / len(self.time_intervals)
        prob_block = self.rejected_calls / len(self.time_intervals)
        avg_delay = sum(self.waiting_time_intervals) / len(self.waiting_time_intervals) if len(self.waiting_time_intervals) > 0 else 0
        
        for i in range(len(self.waiting_time_intervals)):
            predicton_error.append(self.waiting_time_intervals[i] - self.avg_waiting[i])

        avg_general_service_time  = sum(self.general_time_intervals) / len(self.general_time_intervals) if len(self.general_time_intervals) > 0 else 0
        avg_specific_service_time = sum(self.specific_time_intervals) / len(self.specific_time_intervals)

        return prob_delay, prob_block, avg_delay, predicton_error, avg_general_service_time, avg_specific_service_time
        
