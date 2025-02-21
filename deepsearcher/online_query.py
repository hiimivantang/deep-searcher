from typing import Tuple, List

from deepsearcher.agent import (
    generate_sub_queries,
    generate_gap_queries,
    generate_final_answer,
)
from deepsearcher.agent.search_vdb import search_chunks_from_vectordb
from deepsearcher.vector_db.base import deduplicate_results, RetrievalResult

# from deepsearcher.configuration import vector_db, embedding_model, llm
from deepsearcher import configuration
from deepsearcher.tools import log
import asyncio


# Add a wrapper function to support synchronous calls
def query(
    original_query: str, max_iter: int = 3
) -> Tuple[str, List[RetrievalResult], int]:
    return asyncio.run(async_query(original_query, max_iter))

async def async_query(
    original_query: str, max_iter: int = 3
) -> Tuple[str, List[RetrievalResult], int]:
    retrieval_res, all_sub_queries, retrieve_conseumed_token = await async_retrieve(
        original_query, max_iter
    )
    ### GENERATE FINAL ANSWER ###
    log.color_print("<think> Generating final answer... </think>\n")
    final_answer, final_consumed_token = generate_final_answer(
        original_query, all_sub_queries, retrieval_res
    )
    log.color_print("\n==== FINAL ANSWER====\n")
    log.color_print(final_answer)
    return final_answer, retrieval_res, retrieve_conseumed_token + final_consumed_token


def retrieve(
    original_query: str, max_iter: int = 3
) -> Tuple[str, List[RetrievalResult], int]:
    return asyncio.run(async_retrieve(original_query, max_iter))


async def async_retrieve(
    original_query: str, max_iter: int = 3
) -> Tuple[List[RetrievalResult], List[str], int]:
    log.color_print(f"<query> {original_query} </query>\n")
    all_search_res = []
    all_sub_queries = []
    total_tokens = 0

    ### SUB QUERIES ###
    sub_queries, used_token = generate_sub_queries(original_query)
    total_tokens += used_token
    if not sub_queries:
        log.color_print("No sub queries were generated by the LLM. Exiting.")
        return [], []
    else:
        log.color_print(
            f"<think> Break down the original query into new sub queries: \n\t{'\n\t'.join(sub_queries)}</think>\n"
        )
    all_sub_queries.extend(sub_queries)
    sub_gap_queries = sub_queries

    for iter in range(max_iter):
        log.color_print(f">> Iteration: {iter + 1}\n")
        search_res_from_vectordb = []
        search_res_from_internet = []  # TODO

        # Create all search tasks
        search_tasks = [
            search_chunks_from_vectordb(query, sub_gap_queries)
            for query in sub_gap_queries
        ]
        # Execute all tasks in parallel and wait for results
        search_results = await asyncio.gather(*search_tasks)
        # Merge all results
        for result in search_results:
            search_res, consumed_token = result
            total_tokens += consumed_token
            search_res_from_vectordb.extend(search_res)

        search_res_from_vectordb = deduplicate_results(search_res_from_vectordb)
        # search_res_from_internet = deduplicate_results(search_res_from_internet)
        all_search_res.extend(search_res_from_vectordb + search_res_from_internet)

        ### REFLECTION & GET GAP QUERIES ###
        log.color_print("<think> Reflecting on the search results... </think>\n")
        sub_gap_queries, consumed_token = generate_gap_queries(
            original_query, all_sub_queries, all_search_res
        )
        total_tokens += consumed_token
        if not sub_gap_queries:
            log.color_print(
                "<think> No new search queries were generated. Exiting. </think>\n"
            )
            break
        else:
            log.color_print(
                f"<think> New search queries for next iteration: {sub_gap_queries} </think>\n"
            )
            all_sub_queries.extend(sub_gap_queries)

    all_search_res = deduplicate_results(all_search_res)
    return all_search_res, all_sub_queries, total_tokens


def naive_retrieve(
    query: str, collection: str = None, top_k=10
) -> List[RetrievalResult]:
    vector_db = configuration.vector_db
    embedding_model = configuration.embedding_model

    if not collection:
        retrieval_res = []
        collections = [
            col_info.collection_name for col_info in vector_db.list_collections()
        ]
        for collection in collections:
            retrieval_res_col = vector_db.search_data(
                collection=collection,
                vector=embedding_model.embed_query(query),
                top_k=top_k // len(collections),
            )
            retrieval_res.extend(retrieval_res_col)
        retrieval_res = deduplicate_results(retrieval_res)
    else:
        retrieval_res = vector_db.search_data(
            collection=collection,
            vector=embedding_model.embed_query(query),
            top_k=top_k,
        )
    return retrieval_res


def naive_rag_query(
    query: str, collection: str = None, top_k=10
) -> Tuple[str, List[RetrievalResult]]:
    llm = configuration.llm
    retrieval_res = naive_retrieve(query, collection, top_k)

    chunk_texts = []
    for chunk in retrieval_res:
        if "wider_text" in chunk.metadata:
            chunk_texts.append(chunk.metadata["wider_text"])
        else:
            chunk_texts.append(chunk.text)
    mini_chunk_str = ""
    for i, chunk in enumerate(chunk_texts):
        mini_chunk_str += f"""<chunk_{i}>\n{chunk}\n</chunk_{i}>\n"""

    summary_prompt = f"""You are a AI content analysis expert, good at summarizing content. Please summarize a specific and detailed answer or report based on the previous queries and the retrieved document chunks.

    Original Query: {query}
    Related Chunks: 
    {mini_chunk_str}
    """
    char_response = llm.chat([{"role": "user", "content": summary_prompt}])
    final_answer = char_response.content
    log.color_print("\n==== FINAL ANSWER====\n")
    log.color_print(final_answer)
    return final_answer, retrieval_res
