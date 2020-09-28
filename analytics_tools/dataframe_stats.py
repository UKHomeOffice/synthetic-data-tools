import os
import sys
import config
import model_config
from db import *
from utils import *
import pandas as pd
from pick import pick
import time
import threading
from functools import partial

def status_update(start):
    global process_timer
    elapsed = round(time.time() - start, 2)
    process_timer = threading.Timer(30.0, partial(status_update, start))
    process_timer.start()
    print("\n%sProcessing data...please wait...elapsed time %s secs...%s\n" % 
        (colour.CYAN, elapsed, colour.END))

os.chdir(sys.path[0])

all_columns = [
    'Name', 
    'Type',
    'Count',
    'Mode',
    'Mean',
    'Median',
    'Max',
    'Min',
    'Sum',
    'Std',
    'Var',
    '10% percentile',
    '25% percentile',
    '50% percentile',
    '75% percentile'
]

input_title = 'What input db to read entries from?'
input_choices = list(config.DATABASES.values())
input_choice, input_index = pick(input_choices, input_title)

db_input = open_database(input_choice)

table_title = 'What dataset are we accessing?'
table_choices = list_tables(db_input, input_choice)
table_choice, table_index = pick(table_choices, table_title)

filename = '_temp_' + table_choice + '.csv'

start = time.time()
status_update(start)

db_input = open_database(input_choice, table_choice)
results = read_entries(db_input, table_choice)

stats_path = (config.STATISTICS_PATH + 
    table_choice + '_statistics.csv')
    
if not os.path.exists(stats_path):
    append_list_as_row(stats_path, all_columns)

generate_csv(db_input, table_choice, results, filename, model_config.IGNORE_COLUMNS)

columns = select_columns(db_input, table_choice, model_config.IGNORE_COLUMNS)
models = model_config.MODELS
field_types = {}

for model in models:
    if table_choice.startswith(model):
        data_fields = models[model]['fields']
    
        for field in data_fields:
            field_types[field] = data_fields[field][model_config.CURRENT_TRAINER]['type']
            
datetime_columns = [k for k,v in field_types.items() if v == 'DateTime']

df = pd.read_csv(filename, parse_dates=datetime_columns)

def process_stats(df, field, field_type):
    stats = {}
    
    for model in models:
        if table_choice.startswith(model):
            trainer = models[model]['fields'][field][model_config.CURRENT_TRAINER]
            ignore_column = trainer.get('ignore_column', False)

    if field_type == 'DateTime':
        convert_to_timestamps = []
        for t in df[field]:
            try:
                timestamp = time.mktime(t.timetuple())
            except:
                timestamp = None
            convert_to_timestamps.append(timestamp)
        df[field] = convert_to_timestamps
    
    if field_type == 'String':
        stats = {
            'Count': df[field].count(),
            'Mode': df[field].mode(dropna=True).get(0, None)
        }
    else:
        stats = {
            'Count': round(df[field].count(), 2),
            'Mode': round(df[field].mode(dropna=True).get(0, 0), 2),
            'Mean': round(df[field].mean(), 2),
            'Median': round(df[field].median(), 2),
            'Max': round(df[field].max(), 2),
            'Min': round(df[field].min(), 2),
            'Sum': round(df[field].sum(), 2),
            'Std': round(df[field].std(), 2),
            'Var': round(df[field].var(), 2),
            '10% percentile': round(df[field].quantile(0.1), 2),
            '25% percentile': round(df[field].quantile(0.25), 2),
            '50% percentile': round(df[field].quantile(0.5), 2),
            '75% percentile': round(df[field].quantile(0.75), 2)
        }
    
    all_stats = [group_field, field_type]
    all_stats += list(stats.values())
    if not ignore_column:
        append_list_as_row(stats_path, all_stats)

for group_field in columns:
    field_type = field_types.get(group_field, 'String')
    process_stats(df, group_field, field_type)

print("\nAnalysed and generated statistics for " + table_choice + "\n")
process_timer.cancel()
os.remove(filename)