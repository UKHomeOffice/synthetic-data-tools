import random 
import os
import sys
import csv
import config
import model_config
import datetime
import time
import pandas as pd
import numpy as np
from pick import pick
from utils import *
import threading
from functools import partial
from db import *
import json

from DataDescriber import DataDescriber
from DataGenerator import DataGenerator
from ModelInspector import ModelInspector
from lib.utils import read_json_file

def status_update(start):
    global process_timer
    elapsed = round(time.time() - start, 2)
    process_timer = threading.Timer(30.0, partial(status_update, start))
    process_timer.start()
    print("\n%sProcessing data...please wait...elapsed time %s secs...%s\n" % 
        (colour.CYAN, elapsed, colour.END))

sys.path.append(os.getcwd() + '/DataSynthesizer/')

input_title = 'What input db to read entries from?'
input_choices = list(config.DATABASES.values())
input_choice, input_index = pick(input_choices, input_title)

db_input = open_database(input_choice)

table_title = 'What dataset are we accessing?'
table_choices = list_tables(db_input, input_choice)
table_choice, table_index = pick(table_choices, table_title)

db_input = open_database(input_choice, table_choice)

modes_title = 'What method of model training would you like to use?'
modes_choices = ['all', 'random','independent', 'correlated']
mode_choice, mode_index = pick(modes_choices, modes_title)

default_path = os.getcwd() + '/data_synth_trainer/'
default_descriptions_path = default_path + 'descriptions/'
default_synthetic_data_path = default_path + 'synthetic_data/'
plots_dir = default_path + 'plots/'
SYNTH_TOOL = 'DataSynthesizer'

temp_file_path = default_path + '_temp_' + table_choice + '.csv'

# ************

# all attributes in csv files are strings but DS can intepret them as different types
# you do not have to specify this but it gives clarity tohow you want DS to treat your fields
config_tables = config.TABLES

for index, table in enumerate(config_tables):
    if table_choice.startswith(table):
        attr_choice = config_tables[index]

data_config = model_config.MODELS[attr_choice]['fields']
attribute_to_datatype = extract_props(data_config, 'type', SYNTH_TOOL)

# ****************

# you do not have to specify these here but it gives clarity to DS to do so
# alternatively you can pass a catch all to DataDescriber(category_threshold=20)
# this will then treat any field with a domain size of < 20 as categorical
# domain size example: 'gender' has values 'M', 'F' and null. It's domain size is therefore 2

# N.B. - due to a bug in DS (i.e. if a field is not categorical it has to have a domain size > 1), 
# unique fields like ids and dates have to be set as categorical unless converted to integer/date format

# N.N.B. - anything categorical will have its own 'compare historgram' plotted and exported as png
# therefore if forced to set as categorical, list is here to ignore fields for histogram generation
ignore_synth_data_columns = extract_props(data_config, 'ignore_column', SYNTH_TOOL)

attribute_is_categorical = extract_props(data_config, 'is_categorical', SYNTH_TOOL)

# unique fields are intepreted as candidate keys from SQL tables
# this needs to be turned off if field can not be coerced to Integer type
candidate_keys = extract_props(data_config, 'is_candidate_key', SYNTH_TOOL)

ignore_synth_columns = list(extract_props(data_config, 'ignore_column', SYNTH_TOOL).keys())

def mode_filepaths(mode, field, name):
    mode_filepaths = {
        'random': {
            'description': default_descriptions_path + 'description_random_' + name + '.json', 
            'data': default_synthetic_data_path + 'synthetic_random_' + name + '.csv'
        },
        'independent': {
            'description': default_descriptions_path + 'description_independent_' + name + '.json', 
            'data': default_synthetic_data_path + 'synthetic_independent_' + name + '.csv'
        },
        'correlated': {
            'description': default_descriptions_path + 'description_correlated_' + name + '.json', 
            'data': default_synthetic_data_path + 'synthetic_correlated_' + name + '.csv'
        }
    }
    return mode_filepaths[mode][field]

def describe_synthetic_data(mode: str, description_filepath: str, data_filepath: str, candidate_keys: object):
    '''
    Describes the synthetic data and saves it to the data/ directory.

    Keyword arguments:
    mode -- what type of synthetic data
    category_threshold -- limit at which categories are considered blah
    description_filepath -- filepath to the data description
    '''
    describer = DataDescriber()

    if mode == 'random':
        describer.describe_dataset_in_random_mode(
            data_filepath,
            attribute_to_datatype=attribute_to_datatype,
            attribute_to_is_categorical=attribute_is_categorical,
            attribute_to_is_candidate_key=candidate_keys)
    
    elif mode == 'independent':
        describer.describe_dataset_in_independent_attribute_mode(
            data_filepath,
            attribute_to_datatype=attribute_to_datatype,
            attribute_to_is_categorical=attribute_is_categorical,
            attribute_to_is_candidate_key=candidate_keys)
    
    elif mode == 'correlated':
        epsilon = model_config.CORRELATED_EPSILON_VALUE

        degree_of_bayesian_network = model_config.CORRELATED_DEGREE_OF_BAYESIAN_NETWORK

        describer.describe_dataset_in_correlated_attribute_mode(
            dataset_file=data_filepath, 
            epsilon=epsilon, 
            k=degree_of_bayesian_network,
            attribute_to_datatype=attribute_to_datatype,
            attribute_to_is_categorical=attribute_is_categorical,
            attribute_to_is_candidate_key=candidate_keys)

    describer.save_dataset_description_to_file(description_filepath)


def generate_synthetic_data(
        mode: str, 
        num_rows: int, 
        description_filepath: str,
        synthetic_data_filepath: str
    ):
    '''
    Generates the synthetic data and saves it to the data/ directory.

    Keyword arguments:
    mode -- what type of synthetic data
    num_rows -- number of rows in the synthetic dataset
    description_filepath -- filepath to the data description
    synthetic_data_filepath -- filepath to where synthetic data written
    '''
    generator = DataGenerator()

    if mode == 'random':
        generator.generate_dataset_in_random_mode(num_rows, description_filepath)
            
    elif mode == 'independent':
        generator.generate_dataset_in_independent_mode(num_rows, description_filepath)
    
    elif mode == 'correlated':
        generator.generate_dataset_in_correlated_attribute_mode(num_rows, description_filepath)

    generator.save_synthetic_data(synthetic_data_filepath)


def compare_histograms(
        mode: str, 
        hospital_ae_df: pd.DataFrame, 
        description_filepath: str,
        synthetic_data_filepath: str
    ):
    '''
    Makes comapirson plots showing the histograms for each column in the 
    synthetic data.

    Keyword arguments:
    mode -- what type of synthetic data
    hospital_ae_df -- DataFrame of the original dataset
    description_filepath -- filepath to the data description
    synthetic_data_filepath -- filepath to where synthetic data written
    '''

    synthetic_df = pd.read_csv(synthetic_data_filepath)

    # Read attribute description from the dataset description file.
    attribute_description = read_json_file(
        description_filepath)['attribute_description']

    inspector = ModelInspector(
        hospital_ae_df, synthetic_df, attribute_description)

    for attribute in synthetic_df.columns:
        figure_filepath = os.path.join(
            plots_dir, 
            mode + '_' + attribute + '.png'
        )
        # need to replace whitespace in filepath for Markdown reference
        figure_filepath = figure_filepath.replace(' ', '_')
        inspector.compare_histograms(attribute, figure_filepath)
            
    return inspector

def compare_pairwise_mutual_information(mode, inspector):
    '''
    Looks at correlation of attributes by producing heatmap
    '''

    figure_filepath = os.path.join(
        plots_dir, 
        'mutual_information_heatmap_' + mode + '.png'
    )

    inspector.mutual_information_heatmap(figure_filepath)

def save_synthetic_data(data, db, table):
    synth_data_df = pd.read_csv(data, na_filter=False, dtype=str)
    columns = synth_data_df.columns
    
    for index, row in synth_data_df.iterrows():
        entry = lambda: None
        
        for column in columns:
            value = getattr(row, column).strip()
            column = column.lower()
    
            field = model_config.MODELS[attr_choice]['fields'][column]
            field_type = field[model_config.CURRENT_TRAINER]['type']
    
            converted_value = convert_type(field_type, value, column)
            setattr(entry, column, converted_value)
            
        columns_lowercase = [column.lower() for column in columns]
        
        write_entry(db, table, entry, columns_lowercase)

def run_trainer(mode_choice):
    prompt = '\nWhat would you like to call your new table?\n(Will be prefixed with "' + table_choice + '_' + mode_choice + '_")\n\n'
    name_choice = input(prompt)
    if name_choice:
        table_name = table_choice + '_' + mode_choice + '_' + name_choice
    else:
        table_name = table_choice + '_' + mode_choice
    
    print('\nWhat version would you like to call the dataset ' + table_name + '?\n(Please check previous version in dataset_processing_meta.csv sheet)\n')
    version_input = input()
    
    print('\nAny additional notes about this version?\n')
    notes_input = input()
    
    start = time.time()
    status_update(start)
    
    if not os.path.exists(temp_file_path):
        results = read_entries(db_input, table_choice)
        generate_csv(db_input, table_choice, results, temp_file_path, ignore_synth_columns)
    
    db_output = open_database(config.DATABASES['synth'], table_name)
    db_output.drop_table(table_name, with_all_data=True)
    db_output.create_tables()
    
    describer = DataDescriber()
    
    data_df = pd.read_csv(temp_file_path)
    num_rows = len(data_df)
    save_file_name = table_choice + '_' + name_choice
    
    print('describing synthetic data for', mode_choice, 'mode...')
    describe_synthetic_data(
        mode_choice, 
        mode_filepaths(mode_choice, 'description', save_file_name), 
        temp_file_path, 
        candidate_keys
    )
    
    print('generating synthetic data for', mode_choice, 'mode...')
    generate_synthetic_data(
        mode_choice, 
        num_rows, 
        mode_filepaths(mode_choice, 'description', save_file_name),
        mode_filepaths(mode_choice, 'data', save_file_name)
    )
    
    print('saving synthetic data to database for', mode_choice, 'mode...')
    save_synthetic_data(
        mode_filepaths(mode_choice, 'data', save_file_name),
        db_output,
        table_name
    )

    print('comparing histograms for', mode_choice, 'mode...')
    inspector = compare_histograms(
        table_name, 
        data_df, 
        mode_filepaths(mode_choice, 'description', save_file_name),
        mode_filepaths(mode_choice, 'data', save_file_name)
    )
    
    print('comparing pairwise mutual information for', mode_choice, 'mode...')
    compare_pairwise_mutual_information(table_name, inspector)
    
    end = time.time()
    elapsed = round(end - start, 2)
    print('done in ' + str(elapsed) + ' seconds.')

    str_cat = 0
    str_not_cat = 0
    int_cat = 0
    int_not_cat = 0
    datetimes = 0

    with open('./data_models/' + attr_choice + '.json') as json_file:
        fields = json.load(json_file)
        for row in fields:
            if fields[row][0] == "str_cat":
                str_cat += 1
            elif fields[row][0] == "str_not_cat":
                str_not_cat += 1
            elif fields[row][0] == "int_cat":
                int_cat += 1
            elif fields[row][0] == "int_not_cat":
                int_not_cat += 1
            elif fields[row][0] == "datetime_not_cat":
                datetimes += 1
    
    entry_csv = [
        table_name,
        table_choice,
        'synth_' + mode_choice,
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
        '',
        str_cat,
        str_not_cat,
        int_cat,
        int_not_cat,
        datetimes
    ]
    
    if mode_choice == 'correlated':
        entry_csv[13] = model_config.CORRELATED_EPSILON_VALUE
        entry_csv[14] = model_config.CORRELATED_DEGREE_OF_BAYESIAN_NETWORK
    
    append_list_as_row(config.SYNTH_META_CSV_PATH, entry_csv)
    
    process_timer.cancel()
    
    print("\n%s%sProcessed %s%s%s data into %s%s%s table in the %ssynth_datasets%s database!%s\n" % 
        (colour.BOLD, colour.GREEN, 
        colour.DARKCYAN, table_choice, colour.GREEN, 
        colour.DARKCYAN, table_name, colour.GREEN, 
        colour.DARKCYAN, colour.GREEN, 
        colour.END))

if mode_choice == 'all':
    for mode in modes_choices:
        if mode != 'all':
            run_trainer(mode)
else:
    run_trainer(mode_choice)

os.remove(temp_file_path)