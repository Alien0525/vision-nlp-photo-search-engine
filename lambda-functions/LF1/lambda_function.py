import json
import boto3
import urllib3
import urllib.parse
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

# Initialize AWS clients
s3_client = boto3.client('s3')
rekognition_client = boto3.client('rekognition')

# --- CONFIGURATION ---
REGION = 'us-east-1' 
HOST = 'search-photos-xxxxx.us-east-1.es.amazonaws.com'  # REPLACE with your OpenSearch endpoint (NO https://)
INDEX = 'photos'
# ------------------------------------

URL = f'https://{HOST}/{INDEX}/_doc'

def lambda_handler(event, context):
    http = urllib3.PoolManager()
    
    # 1. Process the S3 PUT Event
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        # Unquote the key in case the file name has spaces
        object_key = urllib.parse.unquote_plus(record['s3']['object']['key'])
        timestamp = record['eventTime']
        
        # 2. Call Rekognition to get AI labels
        rek_response = rekognition_client.detect_labels(
            Image={
                'S3Object': {'Bucket': bucket, 'Name': object_key}
            },
            MaxLabels=10,
            MinConfidence=75
        )
        
        labels = []
        for label in rek_response['Labels']:
            labels.append(label['Name'].lower())
            
        # 3. Call S3 head_object to get custom user metadata
        head_response = s3_client.head_object(Bucket=bucket, Key=object_key)
        metadata = head_response.get('Metadata', {})
        
        # boto3 automatically lowercases custom metadata keys (x-amz-meta-customlabels -> customlabels)
        custom_labels = metadata.get('customlabels', '')
        if custom_labels:
            # Assume custom labels are comma separated
            custom_list = [l.strip().lower() for l in custom_labels.split(',')]
            labels.extend(custom_list)
            
        # Remove any duplicate labels
        labels = list(set(labels))
            
        # 4. Construct JSON Document to store in OpenSearch
        document = {
            "objectKey": object_key,
            "bucket": bucket,
            "createdTimestamp": timestamp,
            "labels": labels
        }
        
        # 5. Sign the HTTP request (SigV4) and send to OpenSearch
        session = boto3.Session()
        credentials = session.get_credentials().get_frozen_credentials()
        
        request = AWSRequest(
            method='POST',
            url=URL,
            data=json.dumps(document),
            headers={'Content-Type': 'application/json', 'Host': HOST}
        )
        
        # Add the SigV4 signature to the request
        SigV4Auth(credentials, 'es', REGION).add_auth(request)
        prepared_request = request.prepare()
        
        # # Fire the HTTP POST request using urllib3
        # response = http.request(
        #     prepared_request.method,
        #     prepared_request.url,
        #     headers=prepared_request.headers,
        #     body=prepared_request.body
        # )
        
        # print(f"File {object_key} indexed!")
        # print("OpenSearch Response:", response.status, response.data.decode('utf-8'))

        print("MOCK SUCCESS: OpenSearch is disabled. Document to index would be:")
        print(json.dumps(document))
        
    return {
        'statusCode': 200,
        'body': json.dumps('Photo indexed successfully!')
    }