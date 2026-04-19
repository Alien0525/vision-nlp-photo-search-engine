import json
import boto3
import urllib3
import urllib.parse
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import os

# Initialize AWS clients
s3_client = boto3.client('s3')
rekognition_client = boto3.client('rekognition')

# --- CONFIGURATION ---
REGION = os.environ.get('AWS_REGION', 'us-east-1')
HOST = os.environ['OPENSEARCH_HOST']  # e.g., 'search-photos-xxxxx.us-east-1.es.amazonaws.com'
INDEX = 'photos'
# ------------------------------------

URL = f'https://{HOST}/{INDEX}/_doc'

def lambda_handler(event, context):
    http = urllib3.PoolManager()
    
    # 1. Process the S3 PUT Event
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        object_key = urllib.parse.unquote_plus(record['s3']['object']['key'])
        timestamp = record['eventTime']
        
        # 2. Call Rekognition to get AI labels
        rek_response = rekognition_client.detect_labels(
            Image={'S3Object': {'Bucket': bucket, 'Name': object_key}},
            MaxLabels=10,
            MinConfidence=75
        )
        
        labels = [label['Name'].lower() for label in rek_response['Labels']]
            
        # 3. Call S3 head_object to get custom user metadata
        head_response = s3_client.head_object(Bucket=bucket, Key=object_key)
        metadata = head_response.get('Metadata', {})
        
        custom_labels = metadata.get('customlabels', '')
        if custom_labels:
            custom_list = [l.strip().lower() for l in custom_labels.split(',')]
            labels.extend(custom_list)
            
        # Remove duplicates
        labels = list(set(labels))
            
        # 4. Construct JSON Document
        document = {
            "objectKey": object_key,
            "bucket": bucket,
            "createdTimestamp": timestamp,
            "labels": labels
        }
        
        print(f"Indexing: {object_key} with labels: {labels}")
        
        # 5. Sign and send to OpenSearch
        session = boto3.Session()
        credentials = session.get_credentials().get_frozen_credentials()
        
        request = AWSRequest(
            method='POST',
            url=URL,
            data=json.dumps(document),
            headers={'Content-Type': 'application/json', 'Host': HOST}
        )
        
        SigV4Auth(credentials, 'es', REGION).add_auth(request)
        prepared_request = request.prepare()
        
        # Send to OpenSearch
        response = http.request(
            prepared_request.method,
            prepared_request.url,
            headers=prepared_request.headers,
            body=prepared_request.body
        )
        
        print(f"OpenSearch Response: {response.status}")
        
        if response.status not in [200, 201]:
            print(f"Error: {response.data.decode('utf-8')}")
        
    return {
        'statusCode': 200,
        'body': json.dumps('Photo indexed successfully!')
    }