# B. Work 
 
# Implement a program in C that generates intervals between the arrival of 
# consecutive events: 
 
#  - inputs:  
#    + lambda 
#    + number of samples  
#  - outputs:  
#    + histogram representing the intervals between the arrival of events 
#    + estimator of the average time between the arrival of events 

import math
import random

class Event:
    def __init__(self, event_type, time):
        self.event_type = event_type
        self.time = time

class Simulation:

    def __init__(self, lambda_=1, miu_=3, samples_nr=1000, T=1000, max_resources=1000):
        self.lambda_ = lambda_
        self.miu_ = miu_
        self.samples_nr = samples_nr
        self.T = T
        self.max_resources = max_resources

        self.events = []
        self.active_calls = 0
        self.rejected_calls = 0

        self.histogram = {}
        self.estimator = 0
        self.time = 0

    def call_arrival(self):

        c = - math.log(random.uniform(0,1)) / self.lambda_
        if c in self.histogram.keys():
            self.histogram[c] += 1
        else:
            self.histogram[c] = 1

        next_arrival = self.time + c
        self.events.append(Event("arrival", next_arrival))

        if self.active_calls < self.max_resources:
            self.active_calls += 1
            next_departure = self.time - math.log(random.uniform(0,1)) / self.miu_
            self.events.append(Event("departure", next_departure))
        else:
            self.rejected_calls += 1

        print("Call Arrival")

    def call_departure(self):

        if self.active_calls > 0:
            self.active_calls -= 1
            print("Call Departure")

    def run(self):

        # Generate random number of active calls
        self.active_calls = random.randint(1, self.samples_nr/5)

        for i in range(self.active_calls):
            time = 0
            next_departure = time - math.log(random.uniform(0,1)) / self.miu_
            self.events.append(Event("departure", next_departure))

        # Generate first arrival
        next_arrival = self.time - math.log(random.uniform(0,1)) / self.lambda_
        self.events.append(Event("arrival", next_arrival))        

        print("Simulation started")

        # Run simulation
        while self.samples_nr > 0:
            event = self.events.pop(0)

            if event.event_type == "arrival":
                self.call_arrival()
            else:
                self.call_departure()

            self.samples_nr -= 1


if __name__ == "__main__":

    sim = Simulation(lambda_=5, samples_nr=1000)
    sim.run()

    print(sim.histogram)