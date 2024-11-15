import sqlite3

conn = sqlite3.connect('simulation_results.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS simulations (
    id INTEGER PRIMARY KEY,
    lambda_ INTEGER NOT NULL,
    gen_resources INTEGER NOT NULL,
    spec_resources INTEGER NOT NULL,
    L INTEGER NOT NULL,
    T INTEGER NOT NULL,
    g_prob_delay REAL,                
    g_prob_block REAL,                
    g_avg_delay REAL,
    g_avg_waiting_time REAL,                 
    g_avg_general_service_time REAL,  
    g_avg_specific_service_time REAL, 
    s_prob_delay REAL,                
    s_prob_block REAL,                
    s_avg_delay REAL,
    s_avg_waiting_time REAL,                 
    s_avg_specific_service_time REAL  
)
''')
conn.commit()

''''''''''''''''''''''''''''''''''''''
'''  SIMULATION HANDLE FUNCTIONS   '''
''''''''''''''''''''''''''''''''''''''

# Function to store simulation metrics in database
def store_simulation(simulation, g_metrics, s_metrics):
    '''
    simulation: Simulation object\n
    g_metrics: list of general system metrics\n
    s_metrics: list of specific system metrics
    ''' 

    cursor.execute('''
    INSERT INTO simulations (lambda_, gen_resources, spec_resources, L, T,\
    g_prob_delay, g_prob_block, g_avg_delay, g_avg_waiting_time, g_avg_general_service_time, g_avg_specific_service_time, s_prob_delay, s_prob_block, s_avg_delay, s_avg_waiting_time, s_avg_specific_service_time)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (simulation.lambda_, simulation.gen_operators, simulation.spec_operators, simulation.queue_length, simulation.T,\
          g_metrics[0], g_metrics[1], g_metrics[2], g_metrics[3], g_metrics[4], g_metrics[5], s_metrics[0], s_metrics[1], s_metrics[2], s_metrics[3], s_metrics[5]))
    conn.commit()

# Function to find simulations with specific statistics
def find_simulation(statistics, min_values, max_values, return_=False):
    '''
    statistics: list of desired statistics: 'g_prob_delay', 'g_prob_block', 'g_avg_waiting_time', 's_avg_delay'\n
    min_values: list of minimum values for each statistic\n
    max_values: list of maximum values for each statistic\n
    Return list with the first of each simulation found with the desired statistics
    '''

    if not all(stat in ['g_prob_delay', 'g_prob_block', 'g_avg_waiting_time', 's_avg_delay'] for stat in statistics):
        print('Invalid statistic')
        return
    
    index = {'g_prob_delay': 6, 'g_prob_block': 7, 'g_avg_waiting_time': 9, 's_avg_delay': 14}

    conditions = []
    params = []
    for statistic, value_min, value_max in zip(statistics, min_values, max_values):
        conditions.append(f"{statistic} BETWEEN ? AND ?")
        params.extend([value_min, value_max])
    
    query = f"SELECT * FROM simulations WHERE {' AND '.join(conditions)}"
    
    cursor.execute(query, params)
    sims = cursor.fetchall()

    # sort sims by gen_resources, spec_resources, L
    sims = sorted(sims, key=lambda x: (x[2], x[3], x[4]))

    dif_sims = []
    for sim in sims:
        sim_pams = (sim[2], sim[3], sim[4])

        different = 1
        for sim_ in dif_sims:
            if (sim_[2], sim_[3], sim_[4]) == sim_pams:
                different = 0
                break

        if different:
            dif_sims.append(sim)
            print(f'gen_resources: {sim[2]}, spec_resources: {sim[3]}, L: {sim[4]} | ' + 
              ' | '.join([f'{statistic}: {round(sim[index[statistic]], 5)}' for statistic in statistics]))
    
    if return_: return dif_sims

def get_simulations_metrics(gen_resources, spec_resources, L):
    cursor.execute('''
    SELECT g_prob_delay, g_prob_block, g_avg_delay, g_avg_waiting_time, g_avg_general_service_time, g_avg_specific_service_time, s_prob_delay, s_prob_block, s_avg_delay, s_avg_waiting_time, s_avg_specific_service_time 
    FROM simulations 
    WHERE gen_resources = ? AND spec_resources = ? AND L = ?
    ''', (gen_resources, spec_resources, L))
    return cursor.fetchall()

    # g_prob_delay                  # [0]
    # g_prob_block                  # [1]
    # g_avg_delay                   # [2]
    # g_avg_waiting_time            # [3]
    # g_avg_general_service_time    # [4]
    # g_avg_specific_service_time   # [5]
    # s_prob_delay                  # [6]
    # s_prob_block                  # [7]
    # s_avg_delay                   # [8]
    # s_avg_waiting_time            # [9]
    # s_avg_specific_service_time   # [10]

# Function to clear database
def clear_db():
    cursor.execute('DELETE FROM simulations')
    conn.commit()
    print('Database cleared')

def db_length():
    cursor.execute('SELECT COUNT(*) FROM simulations')
    return cursor.fetchone()[0]




