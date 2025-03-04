import os
import json
from typing import Dict, List, Union
import boto3
from deepsearcher.llm.base import BaseLLM, ChatResponse

class Bedrock(BaseLLM):
    def __init__(self, model: str = "amazon.nova-micro-v1:0", **kwargs):
        self.model = model

        aws_access_key_id = kwargs.pop("aws_access_key_id", os.getenv("AWS_ACCESS_KEY_ID"))
        aws_secret_access_key = kwargs.pop("aws_secret_access_key", os.getenv("AWS_SECRET_ACCESS_KEY"))
        
        region_name = kwargs.pop("region_name", os.getenv("region_name"))

        self.client = boto3.client(
            service_name="bedrock-runtime",
            region_name=region_name, #FIXME
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )
    
    def __str__(self):
        return self.model
        
    def format_prompt_content(self, content: str) -> Union[str, List[Dict]]:
        """Format prompt content specifically for Bedrock models like Nova"""
        if self.model in ["amazon.nova-micro-v1:0"]:
            if isinstance(content, list):
                # Already formatted properly
                return content
            else:
                return [{'text': content}]
        return content
        
    def create_user_message(self, content: Union[str, List[Dict]]) -> Dict:
        """Create a properly formatted user message for Bedrock models"""
        return {"role": "user", "content": content}

    def chat(self, messages: List[Dict]) -> ChatResponse:        
        inference_config = {
            "maxTokens": 5000,  # Adjust as needed
            "temperature": 0.7,  # Adjust as needed
            # Add other parameters as required
        }
        
        # Format the messages properly for Bedrock
        formatted_messages = []
        for message in messages:
            role = message["role"]
            if role == "user":
                # For Nova models, content must be a list of dictionaries
                if self.model in ["amazon.nova-micro-v1:0"]:
                    content = self.format_prompt_content(message["content"])
                    formatted_messages.append({"role": role, "content": content})
                else:
                    formatted_messages.append(message)
            else:
                formatted_messages.append(message)
        
        completion = self.client.converse(
            modelId=self.model, 
            messages=formatted_messages,
            inferenceConfig=inference_config)
        
        content = completion["output"]["message"]["content"][0]["text"]
        total_tokens = completion['usage']['totalTokens']
        return ChatResponse(content=content, total_tokens=total_tokens)
