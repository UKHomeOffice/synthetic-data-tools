import os
import boto3
import pony.orm as pny
from pony.orm.core import Index
import config
import model_config
import anon_tools
import json
import re
from csv import writer
from utils import *
import time
import datetime

def db_factory(db, table_name, generic_fields=[]):
    fields = { '_table': table_name }
    
    if len(generic_fields):
        for field in generic_fields:
            fields[field] = pny.Optional(str)
    else:
        models = model_config.MODELS
        
        for model in models:
            if table_name.startswith(model):
                data_fields = models[model]['fields']
    
                for field in data_fields:
                    fields[field] = data_fields[field]['pny']()

    # if you want to add indexes, example below
    # fields['_indexes_'] = [Index(fields['first_name'],fields['last_name'],is_pk=False,is_unique=False)]
    type(table_name.upper(),(db.Entity,),fields)

def open_database(database, table_name=None, fields=[]):
    db = pny.Database()

    if table_name:
        db_factory(db, table_name, fields)

    db.bind(
        provider='postgres', 
        user=os.environ['DB_USER'], 
        password=os.environ['DB_PASS'], 
        host=os.environ['DB_HOST'],
        port=os.environ['DB_PORT'],
        database=database
    )
    db.generate_mapping(create_tables=True)
    return db

@pny.db_session
def count_rows(db, table):
    select_rows_query = "select count(*) from "
    return db.select(select_rows_query + table)[0]
    
@pny.db_session
def select_columns(db, table, ignore_columns=[]):
    select_columns_query = "select column_name from INFORMATION_SCHEMA.COLUMNS where TABLE_NAME='"
    columns = db.select(select_columns_query + table + "'")
    
    for column in columns:
        if column in ignore_columns:
            columns.remove(column)
            
    return columns

@pny.db_session
def get_table_size(db, table):
    table_size_query = "select pg_size_pretty(pg_relation_size('" + table + "'))"
    return db.select(table_size_query)[0]

@pny.db_session
def select_tables(db, name):
    select_tables_query = ("SELECT table_name " 
        "FROM information_schema.tables "
        "WHERE table_type = 'BASE TABLE' AND table_catalog ='" + name + "';")
    return db.select(select_tables_query)

@pny.db_session     
def convert_to_object(data, columns):
    entry = {}
    for column in columns:
        entry[column] = getattr(data, column, None)
    return entry

@pny.db_session
def write_entry(db, table, data, columns):
    entry = convert_to_object(data, columns)
    getattr(db, table.upper())(**entry)

@pny.db_session
def read_entries(db, table):
    return pny.select(i for i in getattr(db, table.upper()))

@pny.db_session
def process_entries(db, table, results, anon_selected=[]):
    columns = select_columns(db, table)
    
    for result in results:
        adjusted = lambda: None
        for column in columns:
            setattr(adjusted, column, getattr(result, column))
        
        # *** ANON PROCESSES HERE ***
        for anon_tool in anon_selected:
            adjusted = getattr(anon_tools, anon_tool)(adjusted)
  
        write_entry(db, table, adjusted, columns)

@pny.db_session
def augment_entries(db, table, results, pregen_results, fields_to_replace=[]):
    columns = select_columns(db, table)
    
    for result in results:
        adjusted = lambda: None
        pregen_result = sample(pregen_results, len(pregen_results), 1)[0]
        
        for column in columns:
            if column in fields_to_replace:
                setattr(adjusted, column, getattr(pregen_result, column))
            else:
                setattr(adjusted, column, getattr(result, column))

        write_entry(db, table, adjusted, columns)
        
@pny.db_session
def append_list_as_row(file_name, list_of_elem):
    # Open file in append mode
    with open(file_name, 'a+', newline='') as write_obj:
        # Create a writer object from csv module
        csv_writer = writer(write_obj)
        # Add contents of list as last row in the csv file
        csv_writer.writerow(list_of_elem)
    
@pny.db_session
def generate_csv(db, table, results, file_path, ignore_synth_columns=[]):
    if os.path.exists(file_path):
        os.remove(file_path)
    
    ignore_all_columns = []
    ignore_all_columns += model_config.IGNORE_COLUMNS
    ignore_all_columns += ignore_synth_columns
    
    columns = select_columns(db, table)
    selected_columns = []
    
    for col in columns:
        if not col in ignore_all_columns:
            selected_columns.append(col)

    append_list_as_row(file_path, selected_columns)
    
    for result in results:
        values_list = []
        for column in selected_columns:
            values_list.append(getattr(result, column))
        append_list_as_row(file_path, values_list)

@pny.db_session
def generate_single_column_csv(results, file_path, column):
    if os.path.exists(file_path):
        os.remove(file_path)

    append_list_as_row(file_path, [column])
    
    for result in results:
        values_list = []
        values_list.append(getattr(result, column))
        append_list_as_row(file_path, values_list)
            
@pny.db_session
def list_tables(db, name):
    tables = select_tables(db, name)
        
    list = []
    
    for table in tables:
        if not table.startswith('pg_') and not table.startswith('sql_'):
            list.append(table)
    
    return list

@pny.db_session
def generate_transcript(file_name, results, fields):
	for data in results:
	    obj = convert_to_object(data, fields)
	    
	    with open(file_name, 'a') as outfile:
	        outfile.write('<|startoftext|>\n')
	        for field in fields:
	            outfile.write(obj[field] + '\n')
	        outfile.write('<|endoftext|>\n')
	        
@pny.db_session
def upload_for_analysis(table_choice, results, field):
    file_name = '_temp_' + table_choice + '_' + field + '.txt'
    s3 = boto3.resource('s3')
    BUCKET = 'pods-notprod'
    
    def send_files(data, idx):
        obj = convert_to_object(data, [field])
        
        with open(file_name, 'w') as f:
            f.write(obj[field])
    
        file = table_choice + '_' + field + '_' + str(idx) + '.txt'
        key = 'gpt2-comprehend-test-uploads/' + file

        now = datetime.datetime.now()
        dt_string = now.strftime("_%d-%m-%Y_%H-%M-%S.%f")
        kibanaId = table_choice + '_' + field + dt_string
        
        metadata = {
            'Metadata': {
                'kibana_index': table_choice + '_' + field,
                'kibana_id': kibanaId
            }
        }
        
        s3.Bucket(BUCKET).upload_file(file_name, key, ExtraArgs=metadata)
        
    # analyse each entry separately because of AWS Transbribe text limit
    for idx, data in enumerate(results):
        send_files(data, idx)
        time.sleep(0.2) # to cater for AWS throttling exceptions
    
    os.remove(file_name)