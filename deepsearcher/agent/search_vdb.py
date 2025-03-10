import ast
from typing import List

from deepsearcher.agent.prompt import get_vector_db_search_prompt

# from deepsearcher.configuration import llm, embedding_model, vector_db 
from deepsearcher import configuration
from deepsearcher.tools import log


RERANK_PROMPT = """Based on the query questions and the retrieved chunk, to determine whether the chunk is helpful in answering any of the query question, you can only return "YES" or "NO", without any other information.
Query Questions: {query}
Retrieved Chunk: {retrieved_chunk}

Is the chunk helpful in answering any of the questions?
"""


async def search_chunks_from_vectordb(query: str, sub_queries: List[str]):
    consume_tokens = 0
    vector_db = configuration.vector_db
    llm = configuration.llm
    embedding_model = configuration.embedding_model
    # query_embedding = embedding_model.embed_query(query)
    collection_infos = vector_db.list_collections()
    vector_db_search_prompt = get_vector_db_search_prompt(
        question=query,
        collection_info=[
            {
                "collection_name": collection_info.collection_name,
                "collection_description": collection_info.description,
            }
            for collection_info in collection_infos
        ],
    )
    chat_response = llm.chat(
        messages=[{"role": "user", "content": vector_db_search_prompt}]
    )
    # Handle the response properly - AWS Bedrock expects a string, not a JSONArray
    try:
        # First try to parse as a Python list directly
        llm_collections = llm.literal_eval(chat_response.content)
        if not isinstance(llm_collections, list):
            # If not a list, convert to a list with a single item
            llm_collections = [chat_response.content.strip()]
    except:
        # If parsing fails, use the raw string as a single collection
        llm_collections = [chat_response.content.strip()]
        
    collection_2_query = {}
    consume_tokens += chat_response.total_tokens

    for collection in llm_collections:
        if isinstance(collection, str):  # Ensure collection is a string
            collection_2_query[collection] = query

    for collection_info in collection_infos:
        # If a collection description is not provided, use the query as the search query
        if not collection_info.description:
            collection_2_query[collection_info.collection_name] = query
        # If the default collection exists, use the query as the search query
        if vector_db.default_collection == collection_info.collection_name:
            collection_2_query[collection_info.collection_name] = query
    log.color_print(
        f"<THINK> Perform search [{query}] on the vector DB collections: {list(collection_2_query.keys())} </THINK>\n"
    )
    all_retrieved_results = []
    for collection, col_query in collection_2_query.items():
        log.color_print(
            f"\U0001F50D Search [{col_query}] in [{collection}]...\n"
        )
        retrieved_results = vector_db.search_data(
            collection=collection, vector=embedding_model.embed_query(col_query)
        )

        accepted_chunk_num = 0
        references = []
        for retrieved_result in retrieved_results:
            chat_response = llm.chat(
                messages=[
                    {
                        "role": "user",
                        "content": RERANK_PROMPT.format(
                            query=", ".join([col_query] + sub_queries),
                            retrieved_chunk=retrieved_result.text,
                        ),
                    }
                ]
            )
            consume_tokens += chat_response.total_tokens
            if chat_response.content.startswith("YES"):
                all_retrieved_results.append(retrieved_result)
                accepted_chunk_num += 1
                references.append(retrieved_result.reference)
        if accepted_chunk_num > 0:
            log.color_print(
                f"\U00002705 Accept {accepted_chunk_num} document chunk(s) from references: \n\t{'\n' + '\t'.join(references)}\n\n\n"
            )
    return all_retrieved_results, consume_tokens

    # vector_db.search_data(collection="deepsearcher", vector=query_embedding)
