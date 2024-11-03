import math
import random
from matplotlib import pyplot
from system import Event, System

class Simulation:

    def __init__(self, lambda_=0.0222, max_resources=3, max_specific_r=3, queue_length=100, T=43200):

        self.lambda_        = lambda_           # arrival rate
        self.T              = T                 # simulation time period

        self.events          = []               # list of events
        self.rejected_calls  = 0                # number of rejected calls
        self.delayed_calls   = 0                # number of delayed calls
        self.time            = 0                # current time of simulation

        self.general_system  = System(max_resources, queue_length, "general")
        self.specific_system = System(max_specific_r, -1, "specific")

        self.time_intervals       = []          # arrival time intervals
        self.delay_time_intervals = []          # delay time intervals
        self.arrival_histogram    = {}
        self.delay_histogram      = {}

    ''''''''''''''''''''''''''''''''''''
    '''      HISTOGRAM FUNCTION      '''
    ''''''''''''''''''''''''''''''''''''

    def generate_arrival_histogram(self, time_intervals):

        delta = 1/5 * 1/self.lambda_
        v_max =   5 * 1/self.lambda_
        self.arrival_histogram = {i: 0 for i in range(0, int(v_max/delta)+1)}   # initialize arrival_histogram

        for interval in time_intervals:
            if interval > v_max:
                continue
            index = int(interval/delta)
            self.arrival_histogram[index] += 1

        n = len(self.arrival_histogram)
        self.arrival_histogram[n] = len(time_intervals)        # store no. of samples

        self.arrival_histogram = {round(k*delta, 3): v for k,v in self.arrival_histogram.items()}   # change keys to represent intervals
        

    ''''''''''''''''''''''''''''''
    '''    LOGIC FUNCTIONS     '''
    ''''''''''''''''''''''''''''''

    def generate_next_arrival(self):

        # Generate proccess type
        u = random.uniform(0, 1)
        if u < 0.3:
            proccess_type = "general"
        else:
            proccess_type = "specific"

        # Generate time interval
        c = - math.log(random.uniform(0, 1)) / self.lambda_         # -1/lambda * ln(u) ; u ~ U(0,1)

        next_arrival = self.time + c                                # generate next arrival time
        self.events.append(Event("arrival", "general", proccess_type, next_arrival))          # add next arrival event

        self.time_intervals.append(c)                                      # store time interval
    
    def run(self):

        # Generate first arrival
        next_arrival = self.time - math.log(random.uniform(0, 1)) / self.lambda_
        self.events.append(Event("arrival", "general", "general", next_arrival))

        # Run simulation
        while self.time < self.T:

            event = self.events.pop(0)                      # get next event
            self.time = event.time

            if event.system == "general":
                if event.type == "arrival":                 # proccess "arrival" event in "general" system
                    print(f'{round(self.time, 3)}:  \t {event.proccess_type} call arrived at system: {event.system}')

                    self.generate_next_arrival()
                    next_departure = self.general_system.arrival(event)
                    if next_departure:
                        self.events.append(next_departure)  # append "departure" event if resources available

                else:
                    print(f'{round(self.time, 3)}:  \t {event.proccess_type} call exited system: {event.system}')

                    next_arrival = self.general_system.departure(event)    # proccess "departure" event in "general" system
                    if next_arrival:
                        self.events.append(next_arrival)                    # append next "arrival" event

            elif event.system == "specific":                # proccess "arrival" event in "specific" system
                if event.type == "arrival":
                    print(f'{round(self.time, 3)}:  \t {event.proccess_type} call arrived at system: {event.system}')

                    next_departure = self.specific_system.arrival(event)
                    if next_departure:
                        self.events.append(next_departure)
            else:
                print(f'{round(self.time, 3)}:  \t {event.proccess_type} call exited system: {event.system}')
                self.specific_system.departure(event)       # proccess "departure" event in "specific" system

            self.events.sort(key=lambda event: event.time)  # sort events by time

        #metrics = self.general_system.get_metrics()

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
    #pyplot.title(f'(' + chr(96+n) + ') Delay histogram, infinite queue, ' + str(5+n) + ' servers')
    pyplot.savefig('hists/histogram' + str(n) + '.png')
    pyplot.show()

if __name__ == "__main__":

    sim = Simulation(max_resources=7, queue_length=30)

    sim.run()

    gen_metrics = sim.general_system.get_metrics()
    spec_metrics = sim.specific_system.get_metrics()


    print(f"No. of generated events: {len(sim.general_system.time_intervals)}")
    print(f'Average gen service time: {gen_metrics[4]}')
    print(f'Average spec service time: {gen_metrics[5]}')
    print(f'Specific system service time: {spec_metrics[5]}')

    # # Run simulation n times
    # n = 30

    # samples_nr = []

    # rejected_calls = []
    # delayed_calls  = []
    
    # block_prob = []
    # delay_prob = []

    # average_delays = []
    # service_levels = []

    # histograms = []

    # for j in range(30):
    #     for i in range(n):
    #         print(f'\n\nSimulation {i+1}')

    #         sim = Simulation(max_resources=7, queue_length=30-j)
    #         sim.run()

    #         samples_nr.append(len(sim.time_intervals))

    #         rejected_calls.append(sim.rejected_calls)               # store number of rejected calls from each simulation
    #         delayed_calls.append(sim.delayed_calls)                 # store number of delayed calls from each simulation

    #         block_prob.append(sim.block_prob_estimator)             # store block probability for each simulation
    #         delay_prob.append(sim.delay_prob_estimator)             # store delay probability for each simulation

    #         average_delays.append(sim.avrg_delay_estimator)         # store average delay for each simulation
    #         service_levels.append(sim.service_level_estimator)      # store service level for each simulation

    #     ''' Export simulation statistics to file '''
    #     data = [n, block_prob, delay_prob, average_delays, service_levels]
    #     export_data(sim, data)

    #     ''' Export histograms to file '''
    #     # sim.delay_histogram.popitem()                               # remove last element from delay_histogram
    #     # histograms.append(sim.delay_histogram)

    #     ''' Get 1% block probability '''
    #     # avg_block_prob = print_statistics(block_prob, None)[0]
    #     # if avg_block_prob > 0.01:
    #     #     print(f'Queue length: {30-j}')
    #     #     break

    #     ''' Reset lists '''
    #     samples_nr = []

    #     rejected_calls = []
    #     delayed_calls  = []
        
    #     block_prob = []
    #     delay_prob = []

    #     average_delays = []
    #     service_levels = []
        
    # ''' Plot histograms '''
    # # for i in range(4):
    # #     plot_histogram(histograms[i], i+1)




    