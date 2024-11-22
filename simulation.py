import math
import random
from matplotlib import pyplot
from system import Event, System
from db_operations import store_simulation

class Simulation:

    def __init__(self, lambda_=80/3600, gen_operators=100, spec_operators=100, queue_length=100, T=5*24*3600):

        self.lambda_ = lambda_              # arrival rate
        self.T       = T                    # simulation time period
        
        self.gen_operators  = gen_operators 
        self.spec_operators = spec_operators
        self.queue_length   = queue_length 

        self.identifier = 0                 # event id
        self.gen_count  = 0
        self.spec_count = 0

        self.events          = []           # list of events (timeline)
        self.time            = 0            # current time of simulation

        self.general_system  = System(gen_operators, queue_length, "general")
        self.specific_system = System(spec_operators, -1, "specific")

    def __str__(self):
        return f"Simulation parameters: \n>> lambda: {self.lambda_}; gen_operators: {self.gen_operators}; spec_operators: {self.spec_operators}; L: {self.queue_length}; T: {self.T}"
        
    ''''''''''''''''''''''''''''''
    '''    LOGIC FUNCTIONS     '''
    ''''''''''''''''''''''''''''''

    def generate_next_arrival(self):

        # Generate proccess type
        u = random.uniform(0, 1)
        if u < 0.3:
            target_system = "general"
            self.gen_count += 1
        else:
            target_system = "specific"
            self.spec_count += 1

        # Generate time interval
        c = - math.log(random.uniform(0, 1)) / self.lambda_         # -1/lambda * ln(u) ; u ~ U(0,1)

        next_arrival_time = self.time + c                                # generate next arrival time
        self.events.append(Event(self.identifier, "arrival", "general", target_system, next_arrival_time))          # add next arrival event
        self.identifier += 1

    def run(self):

        # Generate first arrival
        self.generate_next_arrival()

        # Run simulation
        while self.time < self.T:

            event = self.events.pop(0)                      # get next event
            self.time = event.time
            #print(event)

            if event.curr_system == "general":
                if event.type == "arrival":                 # proccess "arrival" event in "general" system
                    #print(f'{round(self.time, 3)}:  \t {event.target_system} call arrived at system: {event.system}')

                    self.general_system.arrival(event, self.events)
                    self.generate_next_arrival()

                else:
                    #print(f'{round(self.time, 3)}:  \t {event.target_system} call exited system: {event.system}')

                    self.general_system.departure(event, self.events)    # proccess "departure" event in "general" system

            elif event.curr_system == "specific":                # proccess "arrival" event in "specific" system
                if event.type == "arrival":
                    #print(f'{round(self.time, 3)}:  \t {event.target_system} call arrived at system: {event.system}')

                    self.specific_system.arrival(event, self.events)
                else:
                    #print(f'{round(self.time, 3)}:  \t {event.target_system} call exited system: {event.system}')
                    #print(self.specific_system.waiting_queue)
                    self.specific_system.departure(event, self.events)       # proccess "departure" event in "specific" system


            self.events.sort(key=lambda event: event.time)  # sort events by time
    
''''''''''''''''''''''''''''''''''''
'''     HISTOGRAM FUNCTIONS      '''
''''''''''''''''''''''''''''''''''''

def generate_histogram(data):

    hist = {}
    for d in data:
        if d > 400: continue

        # Find the nearest multiple of 2
        key = 2 * round(d/2)
        
        if key in hist:
            hist[key] += 1
        else:
            hist[key] = 1

    return hist

def plot_histogram(hist, n):

    pyplot.bar(hist.keys(), hist.values(), width=2, align='edge', edgecolor='black')
    # outline bars
    pyplot.title('Prediction Error Distribution')
    pyplot.xlabel('Time (s)')
    pyplot.ylabel('Number of calls')
    pyplot.savefig('hists/histogram' + str(n) + '.png')
    pyplot.show()

def main1():
    lambda_        = 80/3600
    gen_operators  = 100
    spec_operators = 100
    queue_length   = 100
    T              = 5*24*3600         

    # for i in range(5):
    #     for j in range(5):
    #         for k in range(5):
    for l in range(30):    
        sim = Simulation(lambda_=lambda_, gen_operators=4, spec_operators=6, queue_length=2, T=T)
        sim.run()

        gen_metrics = sim.general_system.get_metrics()
        spec_metrics = sim.specific_system.get_metrics()

        store_simulation(sim, gen_metrics, spec_metrics)   # store simulation data in database
        print(f">> Simulation {l+1} completed")
        # print(f">> Iteration {i+1} completed <<")

def main2():

    for i in range(9):
        lambda_        = (60+5*i)/3600
        gen_operators  = 4
        spec_operators = 5
        queue_length   = 2
        T              = 10*24*3600

        sim = Simulation(lambda_=lambda_, gen_operators=gen_operators, spec_operators=spec_operators, queue_length=queue_length, T=T)
        sim.run()

        gen_metrics = sim.general_system.get_metrics()
        spec_metrics = sim.specific_system.get_metrics()

        print("\nLambda: ", lambda_*3600)
        print("Total average delay: ", gen_metrics[2] + spec_metrics[2] + gen_metrics[5])

    

    # error = gen_metrics[6]
    # avg_error = sum(error) / len(error)
    # print(avg_error)

    # hist_waiting = generate_histogram(waiting_time)
    # plot_histogram(hist_waiting, 1)

    # hist_error = generate_histogram(error)
    # plot_histogram(hist_error, 2)

    # print(sim.general_system.received_calls)
    # print(len(sim.general_system.call_history))

    # print(f'>> {round(gen_metrics[0], 4)},  \t{round(gen_metrics[1], 4)},  \t{round(gen_metrics[2], 4)},  \t{round(gen_metrics[3], 4)},  \t{round(gen_metrics[4], 4)}')
    # print(f'>> {round(spec_metrics[0], 4)}, \t{round(spec_metrics[1], 4)}, \t{round(spec_metrics[2], 4)}, \t{round(spec_metrics[3], 4)}, \t{round(spec_metrics[4], 4)}')

if __name__ == "__main__":

    #main1()
    main2()

