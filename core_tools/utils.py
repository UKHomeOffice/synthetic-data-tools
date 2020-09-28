import json
from functools import partial
from dateutil import parser
import datetime
import random

class colour:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'

def extract_props(obj, key_type, trainer):
   new_obj = {}

   for k in obj:
        trainer_obj = obj[k][trainer]
        if key_type in trainer_obj:
            new_obj[k] = trainer_obj[key_type]
       
   return new_obj

def convert_to_datetime(date_str):
   try:
      return parser.parse(date_str).strftime("%Y-%m-%d %H:%M:%S")
   except:
      return datetime.datetime.fromtimestamp(round(float(date_str)))

def convert_to_int(int_str):
   remove_chars = ['$',',']
   
   for char in remove_chars:
      int_str = int_str.replace(char,'')
   
   return round(float(int_str))

def convert_to_bool(bool_str):
   return bool_str.lower() == 'true'

def convert_type(type_str, value_str, column, isBool=False):
   if isBool:
      return value_str.lower() == 'true' if value_str else None
      
   if type_str == 'String':
      return value_str
   
   if not value_str:
      return None

   converter = {
      'Integer': partial(convert_to_int, value_str),
      'Boolean': partial(convert_to_bool, value_str),
      'DateTime': partial(convert_to_datetime, value_str)
   }
   return converter.get(type_str, 'Invalid Type!')()

def save_field_mappings(file_name, fields):
   data = {}
   for idx, val in enumerate(fields):
      data[str(idx)] = val
      
   with open(file_name, 'w') as outfile:
      json.dump(data, outfile)
      
def sample(it, length, k):
    indices = random.sample(range(length), k)
    result = [None] * k
    for index, datum in enumerate(it):
        if index in indices:
            result[indices.index(index)] = datum
    return result