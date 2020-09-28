import datetime
import time
import pony.orm as pny
from pick import pick
import config
from db import *
from utils import *
import config
import model_config
import threading

def status_update(start):
    global process_timer
    elapsed = round(time.time() - start, 2)
    process_timer = threading.Timer(30.0, partial(status_update, start))
    process_timer.start()
    print("\n%sProcessing data...please wait...elapsed time %s secs...%s\n" % 
        (colour.CYAN, elapsed, colour.END))

pregen_db = config.DATABASES['pregen']

input_title = 'What input db to read entries from?'
input_choices = list(config.DATABASES.values())
input_choice, input_index = pick(input_choices, input_title)

db_input = open_database(input_choice)

table_title = 'What dataset are we accessing?'
table_choices = list_tables(db_input, input_choice)
table_choice, table_index = pick(table_choices, table_title)

db_input = open_database(input_choice, table_choice)

db_pregen_input = open_database(pregen_db)

pregen_table_title = 'Which pregenerated dataset do you want to augment in?'
pregen_table_choices = list_tables(db_pregen_input, pregen_db)
pregen_table_choice, pregen_table_index = pick(pregen_table_choices, pregen_table_title)

pregen_fields = select_columns(db_pregen_input, pregen_table_choice, model_config.IGNORE_COLUMNS)

db_pregen_input = open_database(pregen_db, pregen_table_choice, pregen_fields)

aug_title = 'What fields do you want to augment in? (Use spacebar to select)'
aug_choices = select_columns(db_input, table_choice)
aug_selected = pick(aug_choices, aug_title, indicator='-->', multiselect=True) if aug_choices else []
aug_selected = list(map(lambda x: x[0], aug_selected))

models = model_config.MODELS
for model in models:
    if table_choice.startswith(model):
        new_table_choice = model

prompt = '\nWhat would you like to call your new table?\n(Will be prefixed with "' + new_table_choice + '_")\n\n'
name_choice = None
while name_choice == None:
    try:
        name_choice = input(prompt) or None
        if name_choice:
            table_name = new_table_choice + '_' + name_choice
            output_choice = config.DATABASES['aug_synth']
            
            db_output = open_database(output_choice)
            output_tables = list_tables(db_output, output_choice)
            
            if table_name in output_tables:
                confirm_prompt = 'This table already exists. Are you sure you want to overwrite?'
                confirm_choice, confirm_index = pick(['Yes', 'No'], confirm_prompt)
                if confirm_choice == 'No':
                    name_choice = None
    except:
        print("Please enter a name!")

print('\nWhat version would you like to call this?\n(Please check previous version in dataset_processing_meta.csv sheet)\n')
version_input = input()

print('\nAny additional notes about this version?\n')
notes_input = input()

start = time.time()
status_update(start)

results = read_entries(db_input, table_choice)
pregen_results = read_entries(db_pregen_input, pregen_table_choice)

db_output = open_database(output_choice, table_name)
db_output.drop_table(table_name, with_all_data=True)
db_output.create_tables()

augment_entries(db_output, table_name, results, pregen_results, aug_selected)

end = time.time()
elapsed = round(end - start, 2)
process_timer.cancel()

entry_csv = [
    table_name,
    table_choice,
    'aug_synth',
    get_table_size(db_output, table_name),
    len(select_columns(db_output, table_name)),
    count_rows(db_output, table_name),
    datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
    elapsed,
    round(start),
    round(end),
    config.EC2_INSTANCE_TYPE,
    version_input,
    notes_input,
    '',
    ''
]

append_list_as_row(config.SYNTH_META_CSV_PATH, entry_csv)

print("\n%s%sProcessed %s%s%s data into %s%s%s table in the %s%s%s database!%s\n" % 
    (colour.BOLD, colour.GREEN, 
    colour.DARKCYAN, table_choice, colour.GREEN, 
    colour.DARKCYAN, table_name, colour.GREEN, 
    colour.DARKCYAN, output_choice, colour.GREEN, 
    colour.END))
