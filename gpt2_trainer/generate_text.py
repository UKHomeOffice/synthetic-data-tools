import os
import sys
import json
import datetime
import time
import gpt_2_simple as gpt2
import config
import re
from db import *
from pick import pick

os.chdir(sys.path[0])

run_name_title = 'What run model do you want to use to generate data?'
run_name_choices = config.GPT_MODEL_RUN_NAMES
run_name_choice, run_name_index = pick(run_name_choices, run_name_title)

output_choice = config.DATABASES['pregen']

print('\nWhat do you want to call your new table?\n')
table_name = input()

print('\nHow many examples would you like to generate?\n')
number_to_generate = int(input())

start = time.time()

sess = gpt2.start_tf_sess()
gpt2.load_gpt2(sess, run_name=run_name_choice)

generated_so_far = 0

print('\nGenerating synth text entries...\n')

while generated_so_far < number_to_generate:
    genText = gpt2.generate(
        sess, 
        run_name=run_name_choice, 
        prefix="<|startoftext|>",
        return_as_list=True
    )[0]

    pattern = re.compile(r"\<\|startoftext\|\>\n(.*)\n\<\|endoftext\|\>", re.DOTALL)
    truncated = pattern.findall(genText)
    
    if len(truncated):
        truncated = truncated[0]
        matches = truncated.split('\n<|endoftext|>\n<|startoftext|>\n')
        
        mappings_dir = os.getcwd() + '/field_mappings/'
        
        with open(mappings_dir + run_name_choice + '.json') as json_file:
            data = json.load(json_file)
            
            for match in matches:
                columns = [None] * len(data)
                result = lambda: None
                values = match.split('\n')
                
                # If synth data does not match mapping, then it is ignored.
                # This could be handled more specifically for each dataset.
                if len(values) == len(data):
                    for i in data:
                        field = data[i]
                        columns[int(i)] = field
                        setattr(result, field, values[int(i)])
                    
                    db_output = open_database(output_choice, table_name, columns)
                    write_entry(db_output, table_name, result, columns)
                    generated_so_far += 1
        
        elapsed = round(time.time() - start, 2)
        
        print('Time elapsed ' + str(elapsed) + ' seconds...\n')
        
        print('Generated ' + str(generated_so_far) + '/' + str(number_to_generate) + ' entries...\n')

entry_csv = [
    table_name,
    generated_so_far,
    round(time.time() - start, 2),
    datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
]

csv_file = os.getcwd() + config.GPT2_GENERATE_CSV_PATH
append_list_as_row(csv_file, entry_csv)