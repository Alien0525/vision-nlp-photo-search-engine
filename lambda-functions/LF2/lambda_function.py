import json
import boto3

# Initialize Lex V2 client
lex_client = boto3.client('lexv2-runtime')

# --- CONFIGURATION (UPDATE THESE) ---
BOT_ID = 'G1DHT1WMGJ'  
BOT_ALIAS_ID = 'TSTALIASID'  # This is the default Test Alias ID
LOCALE_ID = 'en_US'
# ------------------------------------

def lambda_handler(event, context):
    query = ""
    
    # 1. Safely extract query from API Gateway event or Test event
    if 'queryStringParameters' in event and event['queryStringParameters'] and 'q' in event['queryStringParameters']:
        query = event['queryStringParameters']['q']
    else:
        # Fallback for direct testing in Lambda console
        query = event.get('q', 'show me dogs and cats')
        
    print(f"User Query: {query}")
    
    # 2. Send query to Amazon Lex
    lex_response = lex_client.recognize_text(
        botId=BOT_ID,
        botAliasId=BOT_ALIAS_ID,
        localeId=LOCALE_ID,
        sessionId='test-session-001',
        text=query
    )
    
    # 3. Extract keywords from Lex V2 response
    keywords = []
    session_state = lex_response.get('sessionState', {})
    intent = session_state.get('intent', {})
    slots = intent.get('slots', {})
    
    if intent.get('name') == 'SearchIntent':
        if slots.get('keywordOne') and slots['keywordOne']:
            keywords.append(slots['keywordOne']['value']['interpretedValue'])
            
        if slots.get('keywordTwo') and slots['keywordTwo']:
            keywords.append(slots['keywordTwo']['value']['interpretedValue'])
            
    print(f"Extracted Keywords from Lex: {keywords}")
    
    # If no keywords were found, return an empty array per assignment requirements
    if not keywords:
        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps([])
        }
        
    # 4. Construct OpenSearch Query (MOCK)
    print("MOCK SUCCESS: OpenSearch is disabled. OpenSearch Query would be:")
    
    # Construct an ElasticSearch boolean query to match ANY of the keywords
    should_clauses = [{"match": {"labels": kw}} for kw in keywords]
    os_query = {
        "query": {
            "bool": {
                "should": should_clauses
            }
        }
    }
    print(json.dumps(os_query))
    
    # Mocking a returned photo array to simulate OpenSearch response
    mock_results = [
        f"https://s3.amazonaws.com/your-bucket-name/mock-photo-{keywords[0]}.jpg"
    ]
    
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*' # Required later for API Gateway/CORS
        },
        'body': json.dumps(mock_results)
    }