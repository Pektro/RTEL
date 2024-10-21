# Implement a program in that generates intervals between the arrival of 
# consecutive events: 
 
#  - inputs:  
#    + lambda 
#    + number of samples  
#  - outputs:  
#    + arrival_histogram representing the intervals between the arrival of events 
#    + arrival_estimator of the average time between the arrival of events 


import math
import random
from matplotlib import pyplot


class Event:
    def __init__(self, event_type, time):
        self.event_type = event_type
        self.time = time


class Simulation:

    def __init__(self, lambda_=3, miu_=0.5, max_resources=1, queue_length=100, max_delay=0.5, T=33333):

        self.lambda_        = lambda_           # arrival rate
        self.miu_           = miu_              # service rate 
        self.T              = T                 # simulation time period
        self.max_resources  = max_resources     # maximum number of system resources
        self.queue_length   = queue_length      # maximum queue length
        self.max_delay      = max_delay         # maximum acceptable delay

        self.events         = []                # list of events
        self.waiting_queue  = []                # list of delayed calls
        self.active_calls   = 0                 # number of active calls
        self.rejected_calls = 0                 # number of rejected calls
        self.delayed_calls  = 0
        self.time           = 0                 # current time

        self.time_intervals       = []          # arrival time intervals
        self.delay_time_intervals = []          # delay time intervals
        self.arrival_histogram    = {}
        self.delay_histogram      = {}

    def generate_arrival_histogram(self):

        delta = 1/5 * 1/self.lambda_
        v_max =   5 * 1/self.lambda_
        self.arrival_histogram = {i: 0 for i in range(0, int(v_max/delta)+1)}   # initialize arrival_histogram

        for interval in self.time_intervals:
            if interval > v_max:
                continue
            index = int(interval/delta)
            self.arrival_histogram[index] += 1

        n = len(self.arrival_histogram)
        self.arrival_histogram[n] = len(self.time_intervals)        # store no. of samples

        self.arrival_histogram = {round(k*delta, 3): v for k,v in self.arrival_histogram.items()}   # change keys to represent intervals

    def generate_delay_histogram(self):

        delta = 1/5 * 1/self.lambda_
        v_max =  10 * 1/self.lambda_
        self.delay_histogram = {i: 0 for i in range(0, int(v_max/delta)+1)}   # initialize delay_histogram

        for interval in self.delay_time_intervals:
            if interval > v_max:
                continue
            index = int(interval/delta)
            self.delay_histogram[index] += 1

        n = len(self.delay_histogram)
        self.delay_histogram[n] = len(self.delay_time_intervals)    # store no. of samples

        self.delay_histogram = {round(k*delta, 3): v for k,v in self.delay_histogram.items()}   # change keys to represent intervals

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
            if (self.queue_length > 0 and len(self.waiting_queue) < self.queue_length) or self.queue_length == -1:
                self.delayed_calls += 1
                self.waiting_queue.append(self.time)                # store delayed call
            else:
                self.rejected_calls += 1                            # update number of rejected calls

    def call_departure(self):

        if self.active_calls > 0:
            self.active_calls -= 1

        if len(self.waiting_queue) > 0:                             # check if there are delayed calls

            arrival = self.waiting_queue.pop(0)                     # remove first call from delayed calls
            self.delay_time_intervals.append(self.time - arrival)   # store delay
            self.active_calls += 1                                  # update number of active calls

            # Generate departure event associated with respective arrival from waiting queue
            s = - math.log(random.uniform(0, 1)) / self.miu_        # -1/miu * ln(u) ; u ~ U(0,1)
            
            next_departure = self.time + s                          # generate next departure time
            self.events.append(Event("departure", next_departure))  # add next departure event
    
    def run(self):

        # Generate first arrival
        next_arrival = self.time - math.log(random.uniform(0, 1)) / self.lambda_
        self.events.append(Event("arrival", next_arrival))  
        self.events.sort(key=lambda event: event.time)

        # Run simulation
        while self.time < self.T:

            event = self.events.pop(0)                      # get next event
            self.time = event.time

            if event.event_type == "arrival":               # process event
                self.call_arrival_exponential()
            else:
                self.call_departure()

            self.events.sort(key=lambda event: event.time)  # sort events by time

        # Generate histograms
        self.generate_arrival_histogram()
        self.generate_delay_histogram()

        # Calculate estimators
        self.arrival_estimator       = sum(self.time_intervals) / len(self.time_intervals)          # e
        self.block_prob_estimator    = self.rejected_calls / len(self.time_intervals)               # Pb
        self.delay_prob_estimator    = self.delayed_calls  / len(self.time_intervals)               # Pd
        self.avrg_delay_estimator    = sum(self.delay_time_intervals) / len(self.time_intervals)    # Am
        self.service_level_estimator = 1 - sum([delay>self.max_delay for delay in self.delay_time_intervals]) / len(self.time_intervals)

        # Print results
        print(">> Simulation ended")
        print(f'Average time between the arrival of events: {self.arrival_estimator} (expected: {1/self.lambda_})')
        print("Number of delayed calls: ", self.delayed_calls)
        print("Number of samples: ", len(self.time_intervals))
        print("Block probability: ", round(self.block_prob_estimator, 3))

def print_statistics(data, f):

    average_prob = sum(data)/n
    standard_dev = math.sqrt(sum([(x - average_prob)**2 for x in data])/(n-1))
    standard_error = standard_dev / math.sqrt(n)        
    confidence_interval = 1.96 * standard_error              # 95% confidence interval

    prompt1 = f'Average: {round(average_prob, 4)}'
    prompt2 = f'Standard deviation: {round(standard_dev, 4)}'
    prompt3 = f'Standard error: {round(standard_error, 4)}'
    prompt4 = f'Confidence interval: {round(average_prob, 4)} +- {round(confidence_interval, 4)}'

    if f == None:
        print(prompt1)
        print(prompt2)
        print(prompt3)
        print(prompt4)

    else:
        f.write(prompt1 + '\t|  ')
        f.write(prompt2 + '\t|  ')
        f.write(prompt3 + '\t|  ')
        f.write(prompt4 + '\t')

    return average_prob, standard_dev, standard_error, confidence_interval

def export_data(sim, data):
    
    with open('block_prob_finder.txt', 'a') as f:       # sim_data.txt / block_prob_finder.txt
        f.write(f'No. of simulations: {data[0]}\n')
        f.write(f'Simulation parameters:\n')
        f.write(f'>> lambda: {sim.lambda_}; miu: {sim.miu_}; max_resources: {sim.max_resources}; queue_length: {sim.queue_length}; max_delay: {sim.max_delay}; T: {sim.T}\n\n')

        f.write("\n===  BLOCK PROB STATISTICS  ===\n")
        print_statistics(data[1], f)

        f.write("\n===  DELAY PROB STATISTICS  ===\n")
        print_statistics(data[2], f)

        # f.write("\n===  WAITING TIME STATISTICS (s) ===\n")       # sim_data.txt
        # print_statistics(data[3], f)

        # f.write("\n===  SERVICE LEVEL STATISTICS ===\n")          # sim_data.txt
        # print_statistics(data[4], f)

        f.write("\n\n")
        f.write("=======================================================\n\n")

    return
    
        
def plot_histogram(hist, n):

    pyplot.bar(hist.keys(), hist.values(), width=0.03, align='edge')
    # add caption
    pyplot.xlabel('Time interval')
    pyplot.ylabel('Frequency')
    pyplot.title(f'(' + chr(96+n) + ') Delay histogram, infinite queue, ' + str(5+n) + ' servers')
    pyplot.savefig('hists/histogram' + str(n) + '.png')
    pyplot.show()

if __name__ == "__main__":

    # Run simulation n times
    n = 30

    samples_nr = []

    rejected_calls = []
    delayed_calls  = []
    
    block_prob = []
    delay_prob = []

    average_delays = []
    service_levels = []

    histograms = []

    for j in range(30):
        for i in range(n):
            print(f'\n\nSimulation {i+1}')

            sim = Simulation(max_resources=7, queue_length=30-j)
            sim.run()

            samples_nr.append(len(sim.time_intervals))

            rejected_calls.append(sim.rejected_calls)               # store number of rejected calls from each simulation
            delayed_calls.append(sim.delayed_calls)                 # store number of delayed calls from each simulation

            block_prob.append(sim.block_prob_estimator)             # store block probability for each simulation
            delay_prob.append(sim.delay_prob_estimator)             # store delay probability for each simulation

            average_delays.append(sim.avrg_delay_estimator)         # store average delay for each simulation
            service_levels.append(sim.service_level_estimator)      # store service level for each simulation

        ''' Export simulation statistics to file '''
        data = [n, block_prob, delay_prob, average_delays, service_levels]
        export_data(sim, data)

        ''' Export histograms to file '''
        # sim.delay_histogram.popitem()                               # remove last element from delay_histogram
        # histograms.append(sim.delay_histogram)

        ''' Get 1% block probability '''
        # avg_block_prob = print_statistics(block_prob, None)[0]
        # if avg_block_prob > 0.01:
        #     print(f'Queue length: {30-j}')
        #     break

        ''' Reset lists '''
        samples_nr = []

        rejected_calls = []
        delayed_calls  = []
        
        block_prob = []
        delay_prob = []

        average_delays = []
        service_levels = []
        
    ''' Plot histograms '''
    # for i in range(4):
    #     plot_histogram(histograms[i], i+1)




    