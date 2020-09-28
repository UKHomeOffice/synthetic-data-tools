import model_config
from os import listdir, getcwd, environ
from os.path import isfile, join, dirname

# ------------------------------------------------------------------
# GENERAL CONFIG

CURRENT_DIR = getcwd() + '/'

EC2_INSTANCE_TYPE = 'm4.4xlarge'

SYNTH_META_CSV_PATH = CURRENT_DIR + 'dataset_processing_meta.csv'
GPT2_META_CSV_PATH = '/meta/gpt2_training_meta.csv'
GPT2_GENERATE_CSV_PATH = '/meta/gpt2_generating_meta.csv'
STATISTICS_PATH = CURRENT_DIR + 'statistics/'

RAW_DATASETS_PATH = environ.get('RAW_DATASETS_FOLDER', dirname(getcwd()) + '/raw_datasets/')

# ------------------------------------------------------------------
# ANONYMISATION CONFIG

ANON_TOOLS = {
    'example_data': [],
    'example_data2': ['name']
}

# ------------------------------------------------------------------
# POSTGRES DATABASE NAMES CONFIG

DATABASES = {
    'raw': 'raw_datasets',
    'input': 'input_datasets',
    'synth': 'synth_datasets',
    'aug_synth': 'augmented_synth_datasets',
    'pregen': 'pregenerated_datasets'
}

# ------------------------------------------------------------------
# DYNAMIC PROCESSING CONFIG TABLE VALUES

DATA_MODELS = CURRENT_DIR + model_config.MODELS_FOLDER

TABLES = [".".join(f.split(".")[:-1]) for f in listdir(DATA_MODELS) if isfile(join(DATA_MODELS, f))]

GPT_MODEL_RUN_NAMES = listdir(CURRENT_DIR + model_config.GPT2_MODELS_FOLDER)
