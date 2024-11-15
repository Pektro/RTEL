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

        next_arrival = self.time + c                                # generate next arrival time
        self.events.append(Event(self.identifier, "arrival", "general", target_system, next_arrival))          # add next arrival event
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

                    self.generate_next_arrival()
                    next_departure = self.general_system.arrival(event)
                    if next_departure:
                        self.events.append(next_departure)  # append "departure" event if resources available

                else:
                    #print(f'{round(self.time, 3)}:  \t {event.target_system} call exited system: {event.system}')

                    next_arrival = self.general_system.departure(event)    # proccess "departure" event in "general" system
                    if next_arrival:
                        self.events.append(next_arrival)                    # append next "arrival" event

            elif event.curr_system == "specific":                # proccess "arrival" event in "specific" system
                if event.type == "arrival":
                    #print(f'{round(self.time, 3)}:  \t {event.target_system} call arrived at system: {event.system}')

                    next_departure = self.specific_system.arrival(event)
                    if next_departure:
                        self.events.append(next_departure)
            else:
                #print(f'{round(self.time, 3)}:  \t {event.target_system} call exited system: {event.system}')
                self.specific_system.departure(event)       # proccess "departure" event in "specific" system

            self.events.sort(key=lambda event: event.time)  # sort events by time
    
''''''''''''''''''''''''''''''''''''
'''     HISTOGRAM FUNCTIONS      '''
''''''''''''''''''''''''''''''''''''

def generate_histogram(data):

    hist = {}
    for d in data:
        if d > 400: continue

        # Find the nearest multiple of 10
        key = (d // 10) * 10
        
        if key in hist:
            hist[key] += 1
        else:
            hist[key] = 1

    return hist

def plot_histogram(hist, n):

    pyplot.bar(hist.keys(), hist.values(), width=5, align='edge')
    # add caption
    pyplot.xlabel('Time interval')
    pyplot.ylabel('Frequency')
    pyplot.savefig('hists/histogram' + str(n) + '.png')
    #pyplot.show()

if __name__ == "__main__":

    lambda_        = 80/3600
    gen_operators  = 100
    spec_operators = 100
    queue_length   = 100
    T              = 5*24*3600         

    for i in range(5):
        #for j in range(5):
            for k in range(10):
                for l in range(10):    
                    sim = Simulation(lambda_=lambda_, gen_operators=1+i, spec_operators=1, queue_length=k+1, T=T)
                    sim.run()

                    gen_metrics = sim.general_system.get_metrics()
                    spec_metrics = sim.specific_system.get_metrics()

                    # store_simulation(sim, gen_metrics, spec_metrics)   # store simulation data in database
       
            print(f'Iteration {i} completed')

            error = gen_metrics[6]
            hist = generate_histogram(error)
            print(hist)
            plot_histogram(hist, i)
            #print(f'Error: {error}')

