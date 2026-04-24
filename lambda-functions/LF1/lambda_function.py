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
HOST = os.environ['OPENSEARCH_HOST'] 
INDEX = 'photos'
# ------------------------------------

def lambda_handler(event, context):
    http = urllib3.PoolManager()
    
    # 1. Process the S3 PUT Event
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        object_key = urllib.parse.unquote_plus(record['s3']['object']['key'])
        timestamp = record['eventTime']
        
        print(f"Processing file: {object_key} from bucket: {bucket}")
        
        # 2. Call Rekognition to get AI labels
        rek_response = rekognition_client.detect_labels(
            Image={'S3Object': {'Bucket': bucket, 'Name': object_key}},
            MaxLabels=10,
            MinConfidence=75
        )
        
        labels = [label['Name'].lower() for label in rek_response['Labels']]
            
        # 3. Call S3 head_object to get custom user metadata
        try:
            head_response = s3_client.head_object(Bucket=bucket, Key=object_key)
            metadata = head_response.get('Metadata', {})
            
            custom_labels = metadata.get('x-amz-meta-customLabels', metadata.get('customlabels', ''))
            if custom_labels:
                custom_list = [l.strip().lower() for l in custom_labels.split(',')]
                labels.extend(custom_list)
        except Exception as e:
            print(f"Error retrieving metadata: {e}")
        
        # Remove duplicates
        labels = list(set(labels))
            
        # 4. Construct JSON Document
        document = {
            "objectKey": object_key,
            "bucket": bucket,
            "createdTimestamp": timestamp,
            "labels": labels
        }
        
        # 5. Sign and send to OpenSearch
        # We use PUT and append the object_key to the URL to prevent duplicates
        document_url = f'https://{HOST}/{INDEX}/_doc/{object_key}'
        
        print(f"Indexing to OpenSearch: {document_url}")
        
        session = boto3.Session()
        credentials = session.get_credentials().get_frozen_credentials()
        
        request = AWSRequest(
            method='PUT',
            url=document_url,
            data=json.dumps(document),
            headers={'Content-Type': 'application/json', 'Host': HOST}
        )
        
        SigV4Auth(credentials, 'es', REGION).add_auth(request)
        prepared_request = request.prepare()
        
        # Send the signed request
        response = http.request(
            prepared_request.method,
            prepared_request.url,
            headers=prepared_request.headers,
            body=prepared_request.body
        )
        
        print(f"OpenSearch Response Status: {response.status}")
        
        if response.status not in [200, 201]:
            print(f"OpenSearch Error: {response.data.decode('utf-8')}")
        
    return {
        'statusCode': 200,
        'body': json.dumps('Photo indexed successfully!')
    }
