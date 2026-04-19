import json
import boto3
import urllib3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import os

# Initialize clients
lex_client = boto3.client('lexv2-runtime')

# --- CONFIGURATION ---
BOT_ID = os.environ['LEX_BOT_ID']
BOT_ALIAS_ID = 'TSTALIASID'
LOCALE_ID = 'en_US'
REGION = os.environ.get('AWS_REGION', 'us-east-1')
HOST = os.environ['OPENSEARCH_HOST']
INDEX = 'photos'
PHOTO_BUCKET = os.environ['PHOTO_BUCKET']
# ------------------------------------

def lambda_handler(event, context):
    # 1. Extract query
    query = event.get('queryStringParameters', {}).get('q', '') if 'queryStringParameters' in event else event.get('q', '')
    
    if not query:
        return {
            'statusCode': 400,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Missing query parameter'})
        }
    
    print(f"Query: {query}")
    
    # 2. Send to Lex
    lex_response = lex_client.recognize_text(
        botId=BOT_ID,
        botAliasId=BOT_ALIAS_ID,
        localeId=LOCALE_ID,
        sessionId='search-session',
        text=query
    )
    
    # 3. Extract keywords
    keywords = []
    session_state = lex_response.get('sessionState', {})
    intent = session_state.get('intent', {})
    slots = intent.get('slots', {})
    
    if intent.get('name') == 'SearchIntent':
        if slots.get('keywordOne'):
            keywords.append(slots['keywordOne']['value']['interpretedValue'])
        if slots.get('keywordTwo'):
            keywords.append(slots['keywordTwo']['value']['interpretedValue'])
            
    print(f"Keywords: {keywords}")
    
    if not keywords:
        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps([])
        }
    
    # 4. Query OpenSearch
    should_clauses = [{"match": {"labels": kw.lower()}} for kw in keywords]
    os_query = {
        "query": {
            "bool": {
                "should": should_clauses
            }
        },
        "size": 100
    }
    
    print(f"OpenSearch Query: {json.dumps(os_query)}")
    
    # Sign and send request
    session = boto3.Session()
    credentials = session.get_credentials().get_frozen_credentials()
    
    url = f'https://{HOST}/{INDEX}/_search'
    
    request = AWSRequest(
        method='POST',
        url=url,
        data=json.dumps(os_query),
        headers={'Content-Type': 'application/json', 'Host': HOST}
    )
    
    SigV4Auth(credentials, 'es', REGION).add_auth(request)
    prepared_request = request.prepare()
    
    http = urllib3.PoolManager()
    response = http.request(
        prepared_request.method,
        prepared_request.url,
        headers=prepared_request.headers,
        body=prepared_request.body
    )
    
    # 5. Parse results
    results = json.loads(response.data.decode('utf-8'))
    hits = results.get('hits', {}).get('hits', [])
    
    image_urls = []
    for hit in hits:
        source = hit['_source']
        bucket = source['bucket']
        key = source['objectKey']
        url = f"https://{bucket}.s3.amazonaws.com/{key}"
        image_urls.append(url)
    
    print(f"Found {len(image_urls)} photos")
    
    return {
        'statusCode': 200,
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps(image_urls)
    }