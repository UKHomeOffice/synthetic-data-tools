import json
from os import listdir, getcwd
from os.path import isfile, join
import datetime
import pony.orm as pny
from functools import partial

# ------------------------------------------------------------------
# GENERAL MODEL CONFIG

MODELS_FOLDER = 'data_models'

# ------------------------------------------------------------------
# DATASYNTHESIZER CONFIG

CURRENT_TRAINER = 'DataSynthesizer'
# Increase epsilon value to reduce the injected noises.
# set epsilon=0 to turn off differential privacy 
CORRELATED_EPSILON_VALUE = 0
# The maximum number of parents in Bayesian network
# i.e., the maximum number of incoming edges.
CORRELATED_DEGREE_OF_BAYESIAN_NETWORK = 1

# ------------------------------------------------------------------
# GPT2 CONFIG

# list of models ["117M", 124M", "345M", "355M", "774M", "1558M"]
GPT2_MODEL_NUMBER = '124M'
GPT2_MODELS_FOLDER = 'gpt2_trainer/checkpoint'
TRAINING_STEPS = 200

# ------------------------------------------------------------------
# POSTEGRES & PONY ORM CONFIG

# SQL & Raw Dataset columns to ignore
IGNORE_COLUMNS = ['id', 'ID']

# Types for Pony ORM to map to SQL
PNY_TYPES = {
    'pny_str_req': partial(pny.Required, str),
    'pny_long_str_req': partial(pny.Required, pny.LongStr),
    'pny_str_opt': partial(pny.Optional, str),
    'pny_long_str_opt': partial(pny.Optional, pny.LongStr),
    'pny_datetime_opt': partial(pny.Optional, datetime.datetime),
    'pny_bool_opt': partial(pny.Optional, bool),
    'pny_int_opt': partial(pny.Optional, int)
}

# ------------------------------------------------------------------
# GENERAL SYNTH MODELS CONFIG

# Types for Synthesizer Models
def process_trainer_types(trainer, field_type):
    if trainer == 'DataSynthesizer':
        TRAINER_TYPES = {
            'str_cat': { 'type': 'String', 'is_categorical': True },
            'str_bool_cat': { 'type': 'String', 'is_boolean': True, 'is_categorical': True },
            'str_not_cat': { 'type': 'String', 'is_categorical': False },
            'int_cat': { 'type': 'Integer', 'is_categorical': True },
            'int_not_cat': { 'type': 'Integer', 'is_categorical': False },
            'datetime_cat': { 'type': 'DateTime', 'is_categorical': True },
            'datetime_not_cat': { 'type': 'DateTime', 'is_categorical': False },
            'ignore_column': { 'ignore_column': True, 'type': 'String' }
        }
    return TRAINER_TYPES[field_type]

# ------------------------------------------------------------------
# DYNAMIC PROCESSING CONFIG VALUES

def set_vals(
        set_trainer_field_type, 
        set_pony_orm_field, 
        is_pony_candidate_key=False
    ):
    type_config = {}
    type_config[CURRENT_TRAINER] = process_trainer_types(CURRENT_TRAINER, set_trainer_field_type)
    type_config[CURRENT_TRAINER]['is_candidate_key'] = is_pony_candidate_key
    type_config['pny'] = PNY_TYPES[set_pony_orm_field]
    return type_config

# not categorical automatically does not create histograms
# ignore removes data and column completely from input/output when synth generated
MODELS = {}
data_models = getcwd() + '/' + MODELS_FOLDER
files = [f for f in listdir(data_models) if isfile(join(data_models, f))]

for model_file in files:
    with open(data_models + '/' + model_file) as json_file:
        fields = json.load(json_file)
        file_no_ext = ".".join(model_file.split(".")[:-1])
        MODELS[file_no_ext] = {}
        MODELS[file_no_ext]['fields'] = fields
        
        for field in MODELS[file_no_ext]['fields']:
            trainer_value = MODELS[file_no_ext]['fields'][field][0]
            pony_orm_value = MODELS[file_no_ext]['fields'][field][1]
            values = set_vals(trainer_value, pony_orm_value)
            MODELS[file_no_ext]['fields'][field] = values
