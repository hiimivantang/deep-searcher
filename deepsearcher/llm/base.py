import ast
import re
from abc import ABC, abstractmethod
from typing import Dict, List, Union

class ChatResponse(ABC):
    def __init__(self, content: str, total_tokens: int) -> None:
        self.content = content
        self.total_tokens = total_tokens
    
    def __repr__(self) -> str:
        return f"ChatResponse(content={self.content}, total_tokens={self.total_tokens})"

class BaseLLM(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def chat(self, messages: List[Dict]) -> ChatResponse:
        pass
        
    def format_prompt_content(self, content: str) -> Union[str, List[Dict]]:
        """
        Format the prompt content based on model requirements.
        Override this method in specific LLM implementations if needed.
        
        Args:
            content: The prompt content as a string
            
        Returns:
            The properly formatted content for this specific model
        """
        return content
        
    def create_user_message(self, content: Union[str, List[Dict]]) -> Dict:
        """
        Create a properly formatted user message for this model.
        Override this method in specific LLM implementations if needed.
        
        Args:
            content: The message content (either string or formatted content)
            
        Returns:
            A properly formatted user message for this model
        """
        return {"role": "user", "content": content}

    @staticmethod
    def literal_eval(response_content: str):
        response_content = response_content.strip()

        # remove content between <think> and </think>, especial for DeepSeek reasoning model
        if "<think>" in response_content and "</think>" in response_content:
            end_of_think = response_content.find("</think>") + len("</think>")
            response_content = response_content[end_of_think:]

        # Special case for empty lists
        if response_content == "[]" or response_content.strip() == "[]":
            return []
            
        # Handle code blocks
        try:
            if response_content.startswith("```") and response_content.endswith("```"):
                if response_content.startswith("```python"):
                    response_content = response_content[9:-3]
                elif response_content.startswith("```json"):
                    response_content = response_content[7:-3]
                elif response_content.startswith("```str"):
                    response_content = response_content[6:-3]
                elif response_content.startswith("```\n"):
                    response_content = response_content[4:-3]
                else:
                    # Just remove any code block markers if we can't identify the specific type
                    response_content = re.sub(r'^```.*?\n', '', response_content)
                    response_content = re.sub(r'\n```$', '', response_content)
            
            # Try direct evaluation
            result = ast.literal_eval(response_content.strip())
            return result
        except:
            # Try extracting JSON/List patterns
            try:
                matches = re.findall(r'(\[.*?\]|\{.*?\})', response_content, re.DOTALL)
                if matches:
                    # Return the first valid match
                    for match in matches:
                        try:
                            return ast.literal_eval(match)
                        except:
                            continue
                            
                # If we reach here, no valid matches were found
                raise ValueError(f"Invalid JSON/List format for response content:\n{response_content}")
            except:
                # Last resort: Check if it's just "[]" surrounded by whitespace or other characters
                if "[]" in response_content:
                    return []
                raise ValueError(f"Invalid JSON/List format for response content:\n{response_content}")
