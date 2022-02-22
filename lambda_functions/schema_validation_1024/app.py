import os
import boto3
import json
import time
from aws_lambda_powertools import Metrics, Logger, Tracer
from botocore.exceptions import ClientError
from openapi_schema_validator import validate

# Get env variables
TABLE_NAME = os.environ['TABLE_NAME']
SCHEMA_REGISTRY = os.environ['SCHEMA_REGISTRY']

# Create bobo3 clients
dynamodb = boto3.resource('dynamodb')
schema_client = boto3.client('schemas')

# lambda power tools
logger = Logger()
tracer = Tracer()
metrics = Metrics(namespace="Test-pipeline", service="validation-only")

# Declare initial variables
logger.info("Initializing DDB Table %s", TABLE_NAME)
table = dynamodb.Table(TABLE_NAME)
cache = {}
schema_version = "1"
backoff = [0, 1,3,6,9,12,15,18,21,24]

@tracer.capture_method
def get_schema_name(id):
    try:
        response = table.get_item(Key={'id': id})
        return response["Item"]["schemaName"]
    except ClientError as e:
        logger.error("Dynamodb Error: %s", e.response['Error']['Message'])

    return None

@tracer.capture_method
def describe_schema(schema_name, schema_id):
    response = schema_client.describe_schema(
        RegistryName= SCHEMA_REGISTRY,
        SchemaName= schema_name,
        SchemaVersion= schema_version
    )

    logger.info(response)
    res = response['Content']
    res = json.loads(res)

    return res["components"]["schemas"]["Event"]


def fetch_schema(schema_name, schema_id):

    for backoff_time in backoff:
        try:
            time.sleep(backoff_time)
            metrics.add_metric(name="backoff-" + str(backoff_time), unit="Seconds", value=backoff_time)
            return  describe_schema(schema_name, schema_id)

        except Exception as e:
            logger.error("Describe Schema Error: %s", e)

            continue

    return None


def validate_schema(data, schema):

    try:
        validate(data, schema)
    except Exception as e:
        logger.error("Validation Error: %s", e)
        return False

    return True


@logger.inject_lambda_context(log_event=True)
@metrics.log_metrics(capture_cold_start_metric=True)
@tracer.capture_lambda_handler
def lambda_handler(event, context):

    t = time.process_time()

    if "body" in event:
        event = json.loads(event["body"])

    schema_id = event["schema_id"]
    data = event["data"]

    #Get schema name from dynamodb

    schema_name = get_schema_name(schema_id)


    elapsed_time_dynamodb = (time.process_time() - t) * 1000
    metrics.add_metric(name="Duration-Dynamodb-" + str(schema_id), unit="Milliseconds", value=elapsed_time_dynamodb)

    if schema_name is None:
        logger.error("Schema %s name does not exist.", schema_name)
        raise Exception("Failed to fetch schema name from dynamodb")

    schema = None

    stating_time_fetch_schema = time.process_time()
    #Retrieve schema from cache. If it is not cached, fetch it from the registry.
    try:
        schema = cache[schema_name]
        logger.info("Schema %s is cached.", schema_name)
        metrics.add_metric(name="Cache-Hit", unit="Count", value=1)

        elapsed_time_schema = (time.process_time() - stating_time_fetch_schema) * 1000
        metrics.add_metric(name="Duration-fetching-schema-" + str(schema_id), unit="Milliseconds", value=elapsed_time_schema)
    except KeyError:
        schema = fetch_schema(schema_name, schema_id)

        if schema is None:
            raise Exception("Failed to fetch schema.")

        cache[schema_name] = schema
        logger.info("Caching %s schema.", schema_name)
        metrics.add_metric(name="Cache-Miss", unit="Count", value=1)

    stating_time_validation = time.process_time()

    validation_result = validate_schema(data, schema)

    if validation_result:
        # pass to eventbridge.
        pass

    elapsed_time_validation = (time.process_time() - stating_time_validation) * 1000
    metrics.add_metric(name="Duration-validation-" + str(schema_id), unit="Milliseconds", value=elapsed_time_validation)

    return {
        "isBase64Encoded": False,
        "statusCode": 200,
        "headers": { "Content-Type": "text/plain" },
        "body": validation_result
    }