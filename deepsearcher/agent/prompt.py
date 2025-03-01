from typing import List


def get_vector_db_search_prompt(
    question: str,
    collection_info: List,
    context: List[str] = None,
):
    return f"""
I provide you with collection_name(s) and corresponding collection_description(s). Please select the collection names that may be related to the question and return a python list of str. If there is no collection related to the question, you can return an empty list.

"QUESTION": {question}
"COLLECTION_INFO": {collection_info}

When you return, you can ONLY return a python list of str, WITHOUT any other additional content. Your selected collection name list is:
"""


def get_reflect_prompt(
   question: str,
   mini_questions: List[str],
   mini_chuncks: List[str],
):
    mini_chunk_str = ""
    for i, chunk in enumerate(mini_chuncks):
        mini_chunk_str += f"""<chunk_{i}>\n{chunk}\n</chunk_{i}>\n"""
    reflect_prompt = f"""Determine whether additional search queries are needed based on the original query, previous sub queries, and all retrieved document chunks. If further research is required, provide a Python list of up to 3 search queries. If no further research is required, return an empty list.

If the original query is to write a report, then you prefer to generate some further queries, instead return an empty list.

    Original Query: {question}
    Previous Sub Queries: {mini_questions}
    Related Chunks: 
    {mini_chunk_str}
    """
   
    
    footer = """Respond exclusively in valid List of str format without any other text."""
    return reflect_prompt + footer


def get_final_answer_prompt(
   question: str, 
   mini_questions: List[str],
   mini_chuncks: List[str],
):
    mini_chunk_str = ""
    for i, chunk in enumerate(mini_chuncks):
        mini_chunk_str += f"""<chunk_{i}>\n{chunk}\n</chunk_{i}>\n"""

    summary_prompt = f"""# Report Generation Prompt

You are an expert research synthesizer tasked with creating an engaging, insightful report on {question} based on the information chunks provided below. Unlike standard AI-generated reports, your goal is to create something that feels like it was written by a thoughtful human expert with deep understanding of the subject.

## INFORMATION CHUNKS:
Previous Sub Queries: {mini_questions}
Related Chunks: 
{mini_chunk_str}

## OUTPUT INSTRUCTIONS:

1. **Pyramid Structure & Narrative Flow:**
   Follow Barbara Minto's Pyramid Principle for structuring your report:
   - Begin with the key conclusion or main message upfront (250-word executive summary)
   - Group supporting ideas into 3-4 main sections that naturally flow from your key conclusion
   - Within each section, present ideas in a logical hierarchy, starting with main points and then supporting details
   - End with a forward-looking conclusion that reinforces the main message
   
   Create seamless transitions between sections and paragraphs, ensuring a cohesive narrative arc throughout the report.

2. **Narrative Development:**
   Transform information into a compelling story. Instead of isolated facts or bullet points, weave information into a coherent narrative with:
   - A clear beginning that establishes the context and importance of the topic
   - A middle section that explores key themes with depth and nuance
   - A meaningful ending that provides closure and leaves readers with valuable insights
   
   Use storytelling techniques such as problem-solution frameworks, case studies, or historical progression to maintain reader engagement.

3. **Depth & Synthesis:**
   Present fewer ideas with greater depth rather than many ideas with shallow treatment. For each key concept:
   - Provide comprehensive explanations (2-3 paragraphs minimum)
   - Analyze connections and relationships between different concepts
   - Include concrete examples, real-world applications, and thoughtful implications
   - Present multiple perspectives or interpretations where appropriate
   
   Synthesize information across different chunks to form integrated insights rather than presenting isolated facts.

4. **Presentation & Style:**
   - Write in a conversational yet authoritative tone with fully developed paragraphs
   - Create 2-3 visual elements (tables, conceptual diagrams described in markdown)
   - Use varied sentence structures and paragraph lengths for readability
   - Use bullet points when they improve readability, especially for lists, features, or steps
   - Incorporate technical information naturally within the narrative flow
   
   The report should read as a thoughtful, integrated narrative with a balance of paragraphs and strategic use of bullet points to enhance clarity and readability.

5. **Practical Application:**
   Throughout the report, emphasize the real-world significance and practical applications of the information. For each major section, address:
   - Why this information matters
   - How it can be applied in practice
   - Limitations or considerations to keep in mind
   - Future implications or developments to watch
   
   This practical focus helps transform technical information into actionable insights.

The final report should be comprehensive yet engaging, technically accurate yet accessible, and structured with well-developed paragraphs and strategic use of bullet points to enhance readability. Each section should contain detailed explanations with a thoughtful balance of narrative paragraphs and structured lists where appropriate.
"""

    return summary_prompt
