## Test Setup Steps

#### 1. Add items to Dynamodb.
```
{
    'id': "100",
    'schemaName': '100kb-test'
}
```

#### 2. Add the schema to the Event Bridge schema registry
- registry name should be mapped to schenmaName field in Dynamodb table.

#### 3. Add the samole test payload to s3 bucket.
- S3 files are only needed when testing with the step function's test setup.

#### 4. Verify the json-validation-performance* lambda function's environment variable.