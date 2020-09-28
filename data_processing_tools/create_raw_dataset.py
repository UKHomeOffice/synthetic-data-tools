import json
import os
import datetime
import time
from os import listdir
from os.path import isfile, join
import pony.orm as pny
from pick import pick
import config
import model_config
import pandas as pd
from utils import *
from db import *
import threading
from functools import partial
import model_config

def status_update(start):
    global process_timer
    elapsed = round(time.time() - start, 2)
    process_timer = threading.Timer(30.0, partial(status_update, start))
    process_timer.start()
    print("\n%sProcessing data...please wait...elapsed time %s secs...%s\n" % 
        (colour.CYAN, elapsed, colour.END))

raw_datasets_folder = config.RAW_DATASETS_PATH
write_db = config.DATABASES['raw']
ignore_data_columns = model_config.IGNORE_COLUMNS

dataset_title = 'What new dataset are we creating?'
dataset_choices = config.TABLES
new_dataset, new_dataset_index = pick(dataset_choices, dataset_title)

input_title = 'What raw dataset do you want to use?'
raw_datasets = [f for f in listdir(raw_datasets_folder) if isfile(join(raw_datasets_folder, f))]
input_choice, input_index = pick(raw_datasets, input_title)

print('\nWhat version would you like to call this?\n(Please check previous version in dataset_processing_meta.csv sheet)\n')
version_input = input()

print('\nAny additional notes about this version?\n')
notes_input = input()

print("\n%sProcessing data...please wait...%s\n" % (colour.CYAN, colour.END))

start = time.time()
status_update(start)

db_output = open_database(write_db, new_dataset)
db_output.drop_table(new_dataset.lower(), with_all_data=True)
db_output.create_tables()
        
data_df = pd.read_csv(raw_datasets_folder + input_choice, na_filter=False, dtype=str)
csv_columns = data_df.columns
write_columns = []

for column in csv_columns:
    if not column in ignore_data_columns:
        write_columns.append(column)

for index, row in data_df.iterrows():
    entry = lambda: None
    
    for column in write_columns:
        value = getattr(row, column)
        column = column.lower()
        value = value.strip()

        field = model_config.MODELS[new_dataset]['fields'][column]
        field_type = field[model_config.CURRENT_TRAINER]['type']
        isBool = field[model_config.CURRENT_TRAINER].get('is_boolean', False)

        converted_value = convert_type(field_type, value, column, isBool)
        
        setattr(entry, column, converted_value)
        
    columns_lowercase = [column.lower() for column in write_columns]
    
    write_entry(db_output, new_dataset, entry, columns_lowercase)

end = time.time()
elapsed = round(end - start, 2)
process_timer.cancel()

entry_csv = [
    new_dataset,
    new_dataset,
    'original',
    get_table_size(db_output, new_dataset),
    len(select_columns(db_output, new_dataset)),
    count_rows(db_output, new_dataset),
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

print("\n%s%sGenerated %s%s%s table in the%s raw_datasets%s database!%s\n" % 
    (colour.BOLD, colour.GREEN, 
    colour.DARKCYAN, new_dataset, colour.GREEN, 
    colour.DARKCYAN, colour.GREEN, 
    colour.END))