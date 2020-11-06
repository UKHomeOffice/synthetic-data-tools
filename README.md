# Synthetic Data Tools

This repo is a collection of tools that can be used to generate synthetic data using DataSynthesizer.

## Setup Python environment on Mac

TOOLING SETUP:
Run the following commands to setup a local Python environment on your Mac:
- sudo easy_install pip
- pip install virtualenv
- sudo /usr/bin/easy_install virtualenv
- brew install python3
- virtualenv venv -p python3
- source venv/bin/activate
- pip install -r requirements.txt

## Setup Postgres
DB SETUP:
Follow this guide to setup a local instance of Postgres with user 'Postgres' to parse and store information locally with the right permissions:
https://gist.github.com/ibraheem4/ce5ccd3e4d7a65589ce84f2a3b7c23a3

TL;DR - If you do not want to have to read the above then do the following:
- brew install postgresql
- brew services start postgresql
- psql postgres

To setup the user for synth tools (**not safe for Production**):
  - postgres=# CREATE ROLE postgres WITH LOGIN PASSWORD 'postgres';
  - postgres=# ALTER ROLE postgres Superuser;

To setup databases to store data based on what is in config.js:
  - postgres=# CREATE database raw_datasets;
  - postgres=# CREATE database input_datasets;
  - postgres=# CREATE database synth_datasets;
  - postgres=# CREATE database augmented_synth_datasets;
  - postgres=# CREATE database pregenerated_datasets;

Then run the following to access postegres with the relevant user:
- psql -U postgres

Useful Commands:
- '\du' - Lists users
- '\l' - Lists databases
- '\c <db_name>' - Connect to database
- '\dt' - List tables
- 'SELECT * FROM <table_name>;' - Displays all rows in table
- 'SELECT COUNT(*) FROM <table_name>;' - Displays count of all rows in table

## Setup ENV VARS
export RAW_DATASETS_FOLDER='<absolute_path_to_directory_containing_raw_csv_files>'
export DB_HOST=127.0.0.1
export DB_PORT=5432
export DB_USER=postgres
export DB_PASS=postgres

## Deactivate
To deactivate the Python environment run this command from anywhere:
- deactivate

## Run
To run just simply run the following bash script to open up a menu in the terminal giving you options:

On first run the following so the project and its references to other files live in PYTHON PATH:
- ./python_path.sh

Then every subsequent time just run:
- ./run.sh

## Configuration
### RAW_DATASETS_FOLDER
An env var needs to be set called 'RAW_DATASETS_FOLDER' for where your raw datasets are stored. These usually need to be .csv files which can be exported from Excel. Tools like DataSynthesizer require a flat data structure so this is not suitable interaction with another database or for relational data. Once that is done datasets will be accessed from the '/raw_datasets' folder in this directory. However these can be adjusted in the config.py file.

### CONFIG.PY FILE:
This is for configuring EC2 types if you are running this tooling in AWS Cloud9 or EC2. Also for naming folders and files for storing metadata of all the processing. Primarily it is used to configure what anonmyisation tools to use for which datasets. Under ANON_TOOLS, the keys here represent the exact same naming convention given to each dataset stored under the data_models folder in the root directory of this repo. The values represent which anonymisation tools are available to each dataset based on what methods have been constructed in the 'core_tools/anon_tools/py' file. I have created an 'example_data' and 'example_data2' file to give the reader a clear idea of what they need to do here.

### MODEL_CONFIG.PY:
This holds logic and implementation of mapping to quickly generate links between the running of the Python scripts and Pony ORM which maps all the data to the correct type and stores in Postgres. The 'process_trainer_types' stores keys with config that are utilised by code in the 'data_processing_tools' folder. This has been setup for DataSynthesizer but can be expanded upon with other synthetic data generation models. All these relate to master config for each dataset chosen that is stored in the 'data_models' folder. For further explanation on this see the DATA_MODELS FOLDER section below.
There are also shortcodes for Pony ORM which pass pony objects to the 'core_tools/db.py' file when data is being processed. Again these map to master config set in the DATA_MODELS FOLDER.
Lastly, there is configuration for DataSynthesizer and GPT2 to drive differences in each process. These can be read about more on in the original repos.

### DATA_MODELS FOLDER:
For any new dataset you want to setup, create a .json file, and name it exactly the same as the new table you want to create when processing the original data file into the 'raw_datasets' database in postgres. This is essentially the first thing you do when you run '.run.sh', select 1 'Process Data Menu', and select 1 again 'Create a new dataset'. Ensure when you do the latter you name the table the same as the .json file you created which links them up. As you can see by the 'examples_data.json' file I have included in the data models folder, you setup json where each key relates to an individual data field, and the values is an array, the first value corresponds to a trainer (Datasynthesizer) shortcode, and the second relates to a PonyORM shortcode. This essentially then acts as config for all other processes meaning the tooling knows how to transform, store and synthesise each data type. This is elaborates on in the model_config.py file. However reading up on the DataSynthesizer and Pony OPM documentation will add further light to how these operate if the reader is unfamiliar with them.

### MENU OPTIONS:
There is hierarchical menu structure for different processes setup in the './run.sh' file. These include:
- Process Menu
- Train/Generate Data Menu
- Analyse Data Menu

*PROCESS MENU*:
- Create a new dataset
- Prepare a dataset for anon/synth generation
- Augment data back into synth datasets using pregenerated text

*TRAIN/GENERATE DATA MENU*:
- Use a dataset to generate data using DataSynthesizer
- Train GPT2 for case description/text analysis
- Generate GPT2 text using a pre-trained model

*ANALYSE DATA MENU*:
- Analyse dataset and generate statistics
- Analyse entities of fields using Transcribe/Elasticsearch
- Fetch and save Kibana entity statistics
