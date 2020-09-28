import os
import sys
import datetime
import time
import gpt_2_simple as gpt2
import config
import json
from pick import pick
import time
import threading
from utils import *
from functools import partial
from db import *
from utils import *

os.chdir(sys.path[0])

model_number = model_config.GPT2_MODEL_NUMBER

input_title = 'What input db to read entries from?'
input_choices = list(config.DATABASES.values())
input_choice, input_index = pick(input_choices, input_title)

db_input = open_database(input_choice)

table_title = 'What dataset are we accessing?'
table_choices = list_tables(db_input, input_choice)
table_choice, table_index = pick(table_choices, table_title)

db_input = open_database(input_choice, table_choice)

confirm_prompt = 'Would you like to train a new model(s)?'
confirm_choice, confirm_index = pick(['Yes', 'No'], confirm_prompt)

columns = select_columns(db_input, table_choice)

if confirm_choice == 'Yes':
    print('\nWhat would you like to call your new GPT2 model(s)?\n(This will be prefixed with ' + table_choice + '_' + model_number + '_)')
    version_name = input()
    run_name_choice = table_choice + '_' + model_number + '_' + version_name
else:
	run_name_title = 'What GPT2 model version would you like to use?'
	run_name_choices = config.GPT_MODEL_RUN_NAMES
	run_name_choice, run_name_index = pick(run_name_choices, run_name_title)

fields_title = 'What fields would you like to train the model on?'
fields_selected = pick(columns, fields_title, indicator='-->', multiselect=True)
fields_selected = list(map(lambda x: x[0], fields_selected))

if not os.path.isdir(os.path.join("models", model_number)):
	print(f"Downloading {model_number} model...")
	gpt2.download_gpt2(model_name=model_number)   # model is saved into current directory under /models/124M/
    
results = read_entries(db_input, table_choice)

start = time.time()

file_name = '_temp_' + run_name_choice + '.txt'

mappings_dir = os.getcwd() + '/field_mappings/'
mappings_file = mappings_dir + run_name_choice + '.json'

save_field_mappings(mappings_file, fields_selected)    
generate_transcript(file_name, results, fields_selected)

sess = gpt2.start_tf_sess()
gpt2.finetune(sess,
              file_name,
              model_name=model_number,
              steps=model_config.TRAINING_STEPS,
              run_name=run_name_choice)
              
end = time.time()
elapsed = round(end - start, 2)

entry_csv = [
    run_name_choice,
    table_choice,
    version_name,
    elapsed,
    count_rows(db_input, table_choice),
    datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
]

csv_file = os.getcwd() + config.GPT2_META_CSV_PATH
append_list_as_row(csv_file, entry_csv)
os.remove(file_name)
