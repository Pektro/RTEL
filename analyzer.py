import math
from db_operations import find_simulation, get_simulations_metrics, clear_db, db_length

''''''''''''''''''''''''''''''''''''
'''     AUXILIARY FUNCTIONS      '''
''''''''''''''''''''''''''''''''''''

def print_statistics(data, str=None, f=None):

    n = len(data)
    average_prob = sum(data)/n
    standard_dev = math.sqrt(sum([(x - average_prob)**2 for x in data])/(n-1))
    standard_error = standard_dev / math.sqrt(n)        
    confidence_interval = 1.96 * standard_error              # 95% confidence interval

    prompt1 = f'Average: {round(average_prob, 4)}'
    prompt2 = f'Standard deviation: {round(standard_dev, 4)}'
    prompt3 = f'Standard error: {round(standard_error, 4)}'
    prompt4 = f'Confidence interval: {round(average_prob, 4)} +- {round(confidence_interval, 4)}'

    if f == None:
        if str: print(str)
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
    
    with open('sim_data.txt', 'a') as f:       # sim_data.txt / block_prob_finder.txt
        f.write(f'No. of simulations: {data[0]}\n')
        f.write(f'Simulation parameters:\n')
        f.write(f'>> lambda: {sim[1]}; gen_operators: {sim[2]}; spec_operators: {sim[3]}; L: {sim[4]}; T: {sim[5]}\n\n')

        f.write("\n===  DELAY PROB STATISTICS  ===\n")
        delay_stat = print_statistics(data[1], f=f)

        f.write("\n===  BLOCK PROB STATISTICS  ===\n")
        block_stat = print_statistics(data[2], f=f)

        # f.write("\n===  WAITING TIME STATISTICS (s) ===\n")       # sim_data.txt
        # print_statistics(data[3], f)

        # f.write("\n===  SERVICE LEVEL STATISTICS ===\n")          # sim_data.txt
        # print_statistics(data[4], f)

        f.write("\n\n")
        f.write("=======================================================\n\n")

    return delay_stat, block_stat

''''''''''''''''''''''''''''''''''''
'''        MAIN FUNCTION         '''
''''''''''''''''''''''''''''''''''''

if __name__ == '__main__':

    dif_sims = find_simulation(['g_prob_block', 'g_prob_delay'], [0.015, 0.18], [0.025, 0.3], True)

    for sim_param in dif_sims:  # sim_param >> gen_resources [2], spec_resources [3], L [4]

        sims_metrics = get_simulations_metrics(sim_param[2], sim_param[3], sim_param[4])    # sims_metrics >> g_prob_delay [0], g_prob_block [1]

        prob_delay = [metrics[0] for metrics in sims_metrics]
        prob_block = [metrics[1] for metrics in sims_metrics]

        data = [len(sims_metrics), prob_delay, prob_block]
        delay_stat, block_stat = export_data(sim_param, data)       # average_prob [0], standard_dev [1], standard_error [2], confidence_interval [3]
        condition1 = delay_stat[0] - delay_stat[3] < 0.183 and delay_stat[0] + delay_stat[3] > 0.183      # Pd = 0.19
        condition2 = block_stat[0] - block_stat[3] < 0.025 and block_stat[0] + block_stat[3] > 0.025      # Pb = 0.02
        

        if condition1 and condition2:
            print(f'\n=======================================\n')
            print(f'gen_resources: {sim_param[2]}, spec_resources: {sim_param[3]}, L: {sim_param[4]}')
            print(f'Block prob: {round(block_stat[0], 5)} +- {round(block_stat[3], 5)}')
            print(f'Delay prob: {round(delay_stat[0], 5)} +- {round(delay_stat[3], 5)}')
