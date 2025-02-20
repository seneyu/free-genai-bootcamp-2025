import boto3
import streamlit as st
from typing import Optional, Dict, Any

# Model ID
MODEL_ID = "amazon.nova-micro-v1:0"  # Using the same model as original

class BedrockChat:
    def __init__(self, model_id: str = MODEL_ID):
        """Initialize Bedrock chat client"""
        self.bedrock_client = boto3.client('bedrock-runtime', region_name="us-east-1")
        self.model_id = model_id
        print("Connected to Bedrock")

    def generate_response(self, message: str, inference_config: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Generate a response using Amazon Bedrock"""
        if inference_config is None:
            inference_config = {"temperature": 0.7}  # Keeping the same temperature as original
            
        messages = [{
            "role": "user",
            "content": [{"text": message}]
        }]
        
        try:
            response = self.bedrock_client.converse(  # Using converse instead of invoke_model
                modelId=self.model_id,
                messages=messages,
                inferenceConfig=inference_config
            )
            return response['output']['message']['content'][0]['text']
            
        except Exception as e:
            print(f"Error: {str(e)}")  
            if st.runtime.exists():  # Only use st.error if streamlit is running
                st.error(f"Error generating response: {str(e)}")
            return None

if __name__ == "__main__":
    print("\nWelcome to French Learning Assistant!")
    print("Type '/exit' to end the conversation\n")
    
    chat = BedrockChat()
    while True:
        user_input = input("You: ")
        if user_input.lower() == '/exit':
            print("\nGoodbye! Thanks for chatting!")
            break
        
        response = chat.generate_response(user_input)
        if response:
            print("Bot:", response)
        else:
            print("Bot: Sorry, I couldn't generate a response. Please try again.")