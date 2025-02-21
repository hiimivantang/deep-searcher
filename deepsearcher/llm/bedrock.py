import os
import json
from typing import Dict, List
import boto3
from deepsearcher.llm.base import BaseLLM, ChatResponse

class Bedrock(BaseLLM):
    def __init__(self, model_id: str = "amazon.nova-pro-v1:0", **kwargs):
        self.model_id = model_id
        self.client = boto3.client(
            service_name="bedrock-runtime",
            region_name=kwargs.get("region_name", os.getenv("AWS_DEFAULT_REGION", "us-east-1")),
            aws_access_key_id=kwargs.get("aws_access_key_id", os.getenv("AWS_ACCESS_KEY_ID")),
            aws_secret_access_key=kwargs.get("aws_secret_access_key", os.getenv("AWS_SECRET_ACCESS_KEY")),
        )

    def chat(self, messages: List[Dict]) -> ChatResponse:
        # Prepare the messages in the required format
        formatted_messages = [{"role": msg["role"], "content": [{"text": msg["content"]}]} for msg in messages]

        # Define inference parameters if needed
        inference_config = {
            "maxTokens": 500,  # Adjust as needed
            "temperature": 0.7,  # Adjust as needed
            # Add other parameters as required
        }

        # Make the API call to Amazon Bedrock
        response = self.client.converse(
            modelId=self.model_id,
            messages=formatted_messages,
            inferenceConfig=inference_config,
        )

        # Extract the response content
        content = response["output"]["message"]["content"][0]["text"]
        total_tokens = response["usage"]["totalTokens"]

        return ChatResponse(content=content, total_tokens=total_tokens)
