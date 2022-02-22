import json
import time
from aws_lambda_powertools import Metrics, Logger, Tracer
from openapi_schema_validator import validate


# lambda power tools
logger = Logger()
tracer = Tracer()
metrics = Metrics(namespace="Test-pipeline", service="validation-only")


@logger.inject_lambda_context(log_event=True)
@metrics.log_metrics(capture_cold_start_metric=True)
@tracer.capture_lambda_handler
def lambda_handler(event, context):

    data = event["data"]
    schema = event["payload"]["schema"]

    validation = True
    try:
        validate(data, schema)
    except Exception as e:
        logger.error("Validation Error: %s", e)
        validation = False

    return {
        "isBase64Encoded": False,
        "statusCode": 200,
        "headers": { "Content-Type": "text/plain" },
        "body": validation
    }