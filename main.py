# Implement a program in that generates intervals between the arrival of 
# consecutive events: 
 
#  - inputs:  
#    + lambda 
#    + number of samples  
#  - outputs:  
#    + histogram representing the intervals between the arrival of events 
#    + estimator of the average time between the arrival of events 

import math
import random
from matplotlib import pyplot

class Event:
    def __init__(self, event_type, time):
        self.event_type = event_type
        self.time = time

class Simulation:

    def __init__(self, lambda_=10, miu_=0.5, samples_nr=1000, T=1000, max_resources=500):
        self.lambda_ = lambda_
        self.miu_ = miu_
        self.samples_nr = samples_nr
        self.T = T
        self.max_resources = max_resources

        self.events = []
        self.active_calls = 0
        self.rejected_calls = 0

        self.histogram = {}
        self.time_plot = {}
        self.estimator = 0
        self.estimator = 0
        self.time = 0

    def call_arrival(self):

        c = - math.log(random.uniform(0,1)) / self.lambda_
        c = round(c, 3)
        if c in self.histogram.keys():
            self.histogram[c] += 1
        else:
            self.histogram[c] = 1

        next_arrival = self.time + c
        self.events.append(Event("arrival", next_arrival))
        
        #sort events by time
        self.events.sort(key=lambda event: event.time)

        self.time_plot[next_arrival] = 1

        if self.active_calls < self.max_resources:
            self.active_calls += 1
            next_departure = self.time - math.log(random.uniform(0,1)) / self.miu_
            self.events.append(Event("departure", next_departure))
            self.events.sort(key=lambda x: x.time)
            self.time_plot[next_departure] = 2
        else:
            self.rejected_calls += 1

    def call_departure(self):

        if self.active_calls > 0:
            self.active_calls -= 1

    def run(self):

        # Simulation parameters
        print(f'Simulation parameters: lambda={self.lambda_}, miu={self.miu_}, samples_nr={self.samples_nr}, T={self.T}, max_resources={self.max_resources}\n')
        print(">> Simulation started")

        # Generate random number of active calls
        self.active_calls = random.randint(1, int(self.samples_nr/5))
        print(f'System started with: {self.active_calls} active calls\n')
        i = self.active_calls
        time = 0

        for j in range(i):
            s = - math.log(random.uniform(0,1)) / self.miu_
            time += s
            next_departure = time
            self.events.append(Event("departure", next_departure))

        # Generate first arrival
        next_arrival = self.time - math.log(random.uniform(0,1)) / self.lambda_
        self.events.append(Event("arrival", next_arrival))  
        self.events.sort(key=lambda event: event.time)

        # Run simulation
        while self.samples_nr + i > 0:
            event = self.events.pop(0)
            self.time = event.time

            if event.event_type == "arrival":
                self.call_arrival()
            else:
                self.call_departure()

            self.samples_nr -= 1

        self.estimator = sum([k*v for k,v in self.histogram.items()]) / sum(self.histogram.values())
        self.estimator = round(self.estimator, 3)

        print(">> Simulation ended")
        print(f'Average time between the arrival of events: {self.estimator} (expected: {1/self.lambda_})')
        print("Number of rejected calls: ", self.rejected_calls)

if __name__ == "__main__":

    sim = Simulation(lambda_=5, samples_nr=2000)
    sim.run()

    hist = pyplot.bar(sim.histogram.keys(), sim.histogram.values(), width=0.01)
    
    pyplot.show()

    