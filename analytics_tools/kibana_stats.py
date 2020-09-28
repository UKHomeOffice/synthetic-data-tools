from pick import pick
from db import *
import config
import json
import boto3
import certifi
import os
from aws_requests_auth.aws_auth import AWSRequestsAuth
from elasticsearch import Elasticsearch, RequestsHttpConnection

# Parameters
REGION = os.getenv('AWS_REGION', default='eu-west-1')
# Pull environment data for the ES domain
esendpoint = os.environ['ES_DOMAIN']

# Create the auth token for the sigv4 signature
session = boto3.session.Session()
credentials = session.get_credentials().get_frozen_credentials()
awsauth = AWSRequestsAuth(
    aws_access_key=credentials.access_key,
    aws_secret_access_key=credentials.secret_key,
    aws_token=credentials.token,
    aws_host=esendpoint,
    aws_region=REGION,
    aws_service='es'
)

# Connect to the elasticsearch cluster using aws authentication. The lambda function
# must have access in an IAM policy to the ES cluster.
es = Elasticsearch(
    hosts=[{'host': esendpoint, 'port': 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    ca_certs=certifi.where(),
    timeout=120,
    connection_class=RequestsHttpConnection
)

input_title = 'What input db to pick dataset from?'
input_choices = list(config.DATABASES.values())
input_choice, input_index = pick(input_choices, input_title)

db_input = open_database(input_choice)

table_title = 'What dataset to pick field from?'
table_choices = list_tables(db_input, input_choice)
table_choice, table_index = pick(table_choices, table_title)

columns = select_columns(db_input, table_choice)
columns.remove('id')

field_title = 'What specific field are you measuring?'
field_choice, field_index = pick(columns, field_title)

kibana_index = table_choice + '_' + field_choice

entity_types = list(es.indices.get_mapping(index=kibana_index)[kibana_index]['mappings']
  ['properties']['entity_count']['properties'].keys())

body = { "size": 0, "aggs": {}}

for entity_type in entity_types:
  field = 'entity_count.' + entity_type
  body['aggs'][entity_type] = { "sum" : { "field" : field } }

totals = es.search(index=kibana_index, body=body)['aggregations']

totals = {k: v['value'] for k, v in totals.items()}

totals = {k: round(v / sum(totals.values()) * 100) for k, v in totals.items()}

with open(config.STATISTICS_PATH + 'entity_analysis.json') as f:
    data = json.load(f)
    
data.update({ kibana_index.upper(): totals })

with open(config.STATISTICS_PATH + 'entity_analysis.json', 'w') as f:
    json.dump(data, f)