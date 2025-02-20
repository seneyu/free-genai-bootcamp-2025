import boto3
import json

def test_bedrock_access():
    try:
        # Create clients
        bedrock = boto3.client('bedrock', region_name="us-west-2")
        runtime = boto3.client('bedrock-runtime', region_name="us-west-2")
        
        print("1. Testing model listing...")
        models = bedrock.list_foundation_models()
        print("✓ Successfully listed models")
        
        print("\n2. Testing model invocation...")
        body = {
            "inputText": "Say hello",
            "textGenerationConfig": {
                "temperature": 0.7,
                "maxTokenCount": 512,
                "topP": 0.9,
            }
        }
        
        response = runtime.invoke_model(
            modelId="amazon.titan-text-express-v1",
            body=json.dumps(body)
        )
        response_body = json.loads(response['body'].read())
        print("✓ Successfully invoked model")
        print("Response:", response_body.get('results', [{}])[0].get('outputText', ''))
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\nDebug info:")
        print(f"AWS Region: {boto3.Session().region_name}")
        
if __name__ == "__main__":
    test_bedrock_access()