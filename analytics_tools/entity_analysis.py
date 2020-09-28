import sys
import os
from db import *
from pick import pick
import config

os.chdir(sys.path[0])

input_title = 'What input db to read entries from?'
input_choices = list(config.DATABASES.values())
input_choice, input_index = pick(input_choices, input_title)

db_input = open_database(input_choice)

table_title = 'What dataset are we accessing?'
table_choices = list_tables(db_input, input_choice)
table_choice, table_index = pick(table_choices, table_title)

columns = select_columns(db_input, table_choice)
columns.remove('id')

if input_choice == config.DATABASES['pregen']:
    db_input = open_database(input_choice, table_choice, columns)
else:
    db_input = open_database(input_choice, table_choice)

field_title = 'What field would you like to analyse with Transcribe/Kibana?'
field_selected, field_index = pick(columns, field_title)

results = read_entries(db_input, table_choice)

upload_for_analysis(table_choice, results, field_selected)
