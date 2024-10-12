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

    def __init__(self, lambda_=200, miu_=125, samples_nr=500, T=1000, max_resources=5, stop_condition=0, mode="exponential"):

        self.lambda_ = lambda_                  # arrival rate
        self.miu_ = miu_                        # service rate  
        self.samples_nr = samples_nr            # desired number of samples
        self.T = T                              # simulation time period
        self.max_resources = max_resources      # maximum number of system resources
        self.stop_condition = stop_condition    # stopping condition: 0 - No. of samples, 1 - Time period
        self.mode = mode                        # mode of simulation: exponential, poisson

        self.events = []                        # list of events
        self.active_calls = 0                   # number of active calls
        self.rejected_calls = 0                 # number of rejected calls
        self.time = 0                           # current time

        self.time_intervals = []
        self.histogram = {}

        self.estimator = 0

    def call_arrival_exponential(self):

        c = - math.log(random.uniform(0, 1)) / self.lambda_         # -1/lambda * ln(u) ; u ~ U(0,1)

        next_arrival = self.time + c                                # generate next arrival time
        self.events.append(Event("arrival", next_arrival))          # add next arrival event

        self.time_intervals.append(c)                               # store time interval

        if self.active_calls < self.max_resources:                  # check if there are resources available
            
            self.active_calls += 1                                  # update number of active calls

            s = - math.log(random.uniform(0, 1)) / self.miu_        # -1/miu * ln(u) ; u ~ U(0,1)

            next_departure = self.time + s                          # generate next departure time
            self.events.append(Event("departure", next_departure))  # add next departure event

        else:
            self.rejected_calls += 1

    # def call_arrival_poisson(self):

    #     delta = 0.001                                               # time interval for Poisson process simulation
    #     last_event_time = self.time                                 # store last event time as the current time

    #     while True:
    #         self.time += delta                                      # increment time by delta at each try

    #         u = random.uniform(0, 1)                                # generate a random number to check if an event occurs

    #         if u < self.lambda_ * delta:                            # check if event occurs
    #             next_arrival = self.time                            # current time becomes the arrival time
    #             self.events.append(Event("arrival", next_arrival))
                
    #             interval = next_arrival - last_event_time           # record the time interval since the last event
    #             self.time_intervals.append(interval)

    #             last_event_time = next_arrival                      # update the last event time to the current event time
    #             break

    #     if self.active_calls < self.max_resources:                  # check if there are resources available

    #         self.active_calls += 1                                  # update number of active calls

    #         s = -math.log(random.uniform(0, 1)) / self.miu_         # -1/miu * ln(u) ; u ~ U(0,1)

    #         next_departure = self.time + s                          # generate next departure time
    #         self.events.append(Event("departure", next_departure))  # add next departure event

    #     else:
    #         self.rejected_calls += 1


    def call_departure(self):

        if self.active_calls > 0:
            self.active_calls -= 1

    def run(self):

        # Print simulation parameters
        #print(f'\n\nSimulation parameters: lambda={self.lambda_}, miu={self.miu_}, samples_nr={self.samples_nr}, T={self.T}, max_resources={self.max_resources}, mode={self.mode}')
        #print(f'Stopping condition: {self.samples_nr} samples\n') if self.stop_condition == 0 else print(f'Stopping condition: {self.T} s\n')
        #print(">> Simulation started")

        # # Generate random number of active calls
        # self.active_calls = random.randint(1, int(self.samples_nr/5))
        # print(f'System started with: {self.active_calls} active calls\n')
        # i = self.active_calls
        # time = 0

        # for j in range(i):                                      # starts the system with i active calls
        #     s = - math.log(random.uniform(0, 1)) / self.miu_     
        #     time += s
        #     next_departure = time
        #     self.events.append(Event("departure", next_departure))

        # Generate first arrival
        next_arrival = self.time - math.log(random.uniform(0, 1)) / self.lambda_
        self.events.append(Event("arrival", next_arrival))  
        self.events.sort(key=lambda event: event.time)

        condition = (self.samples_nr > 0) if self.stop_condition == 0 else (self.time < self.T)

        # Run simulation
        while condition:

            event = self.events.pop(0)                      # get next event
            self.time = event.time

            #print(f'{round(event.time, 3)}: {event.event_type}, active calls: {self.active_calls}')

            if event.event_type == "arrival":               # process event
                if self.mode == "exponential":
                    self.call_arrival_exponential()
                # else:
                #     self.call_arrival_poisson()
                self.samples_nr -= 1

            else:
                self.call_departure()

            self.events.sort(key=lambda event: event.time)  # sort events by time

            condition = (self.samples_nr > 0) if self.stop_condition == 0 else (self.time < self.T)

        # Generate histogram
        delta = 1/5 * 1/self.lambda_
        v_max =   5 * 1/self.lambda_
        self.histogram = {i: 0 for i in range(0, int(v_max/delta)+1)}   # initialize histogram

        for interval in self.time_intervals:
            if interval > v_max:
                continue
            index = int(interval/delta)
            self.histogram[index] += 1

        n = len(self.histogram)
        self.histogram[n] = len(self.time_intervals)                    # store no. of samples

        self.histogram = {round(k*delta, 3): v for k,v in self.histogram.items()}   # change keys to represent intervals

        # Calculate estimator
        self.estimator = sum(self.time_intervals) / len(self.time_intervals)

        # Print results
        print(">> Simulation ended")
        print(f'Average time between the arrival of events: {self.estimator} (expected: {1/self.lambda_})')
        print("Number of rejected calls: ", self.rejected_calls)
        print("Number of samples: ", len(self.time_intervals))
        print("Block probability: ", round(self.rejected_calls / len(self.time_intervals)*100, 3))


if __name__ == "__main__":

    # Run simulation n times
    n = 30
    samples_nr = []
    rejected_calls = []
    block_prob = []
    for i in range(n):
        print(f'\n\nSimulation {i+1}')
        sim = Simulation(mode="exponential", stop_condition=1, T=100)
        sim.run()
        samples_nr.append(len(sim.time_intervals))
        rejected_calls.append(sim.rejected_calls)
        block_prob.append(sim.rejected_calls / len(sim.time_intervals)*100)

    # statistics
    average_prob = sum(block_prob)/n
    standard_dev = math.sqrt(sum([(x - average_prob)**2 for x in block_prob])/(n-1))
    standard_error = standard_dev / math.sqrt(n)        
    confidence_interval = 1.96 * standard_error              # 95% confidence interval

    print(f'\n\nAverage number of samples: {round(sum(samples_nr)/n, 2)}')
    print(f'Average number of rejected calls: {round(sum(rejected_calls)/n, 2)}')
    print(f'Average block probability: {round(average_prob, 3)}')
    print(f'Standard deviation: {round(standard_dev, 3)}')
    print(f'Standard error: {round(standard_error, 3)}')
    print(f'Confidence interval: {round(average_prob, 3)} +- {round(confidence_interval, 3)}')
        
    # events_num = sim.histogram.popitem()        # remove last element from histogram
    # hist = pyplot.bar(sim.histogram.keys(), sim.histogram.values(), width=0.03, align='edge')
    #add caption
    # pyplot.xlabel('Time interval')
    # pyplot.ylabel('Frequency')
    # pyplot.title('(a) Exponential distribution, 50 samples')
    # pyplot.show()

