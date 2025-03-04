import ast
from typing import List, Tuple

# from deepsearcher.configuration import llm
from deepsearcher.agent.prompt import get_reflect_prompt
from deepsearcher.vector_db.base import RetrievalResult
from deepsearcher import configuration


def generate_gap_queries(
    original_query: str, all_sub_queries: List[str], all_chunks: List[RetrievalResult]
) -> Tuple[List[str], int]:
    llm = configuration.llm
    reflect_prompt = get_reflect_prompt(
        question=original_query,
        mini_questions=all_sub_queries,
        mini_chuncks=[chunk.text for chunk in all_chunks],
    )
    chat_response = llm.chat([{"role": "user", "content": reflect_prompt}])
    response_content = chat_response.content
    
    try:
        result = llm.literal_eval(response_content)
        # Ensure we always return a list, not a tuple
        if isinstance(result, tuple):
            result = list(result)
        elif not isinstance(result, list):
            # If it's not a list or tuple, make it a single-item list
            result = [result] if result else []
        return result, chat_response.total_tokens
    except Exception as e:
        # If we can't parse the response, return an empty list
        return [], chat_response.total_tokens
