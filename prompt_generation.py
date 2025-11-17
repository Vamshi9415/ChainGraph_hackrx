import re
import logging
from typing import Dict, List
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from language_utils import get_language_name
import json
import requests
from bs4 import BeautifulSoup
# Import ProcessedDocument from its module (update the import path as needed)
from data_models import ProcessedDocument
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import tool
from langchain_community.document_loaders import WebBaseLoader
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.runnables import RunnableParallel, RunnableLambda

from data_frame import DataFrameTools
from model_init import llm 
from document_processors import TargetedDocumentProcessor

# Add these imports at the top of your file with other imports


# Import for document type detection
from document_type_detector import detect_document_type_http

# Import for constants
from config import RERANK_AVAILABLE

# Import for model access
from model_init import embeddings_fast, embeddings_accurate, reranker, llm

# Import for chunking
from adaptive_chunking import UniversalAdaptiveChunking

# Import for document processing
from document_processors import TargetedDocumentProcessor

# Import for query analysis
from query_analyzer import UniversalQueryAnalyzer

# Import for table tools
from data_frame import DataFrameTools

# Import for vector stores
from langchain_community.vectorstores import FAISS

from async_logger import log_document_async, log_questions_async, log_answers_async

# Import detect_document_type_http (update the import path as needed)


# --- UNIVERSAL PROMPT GENERATION ---
def generate_universal_adaptive_prompt(detected_language: str, query_analysis: Dict) -> str:
    """Generate adaptive prompt based on query characteristics"""
    
    language_name = get_language_name(detected_language).upper()
    
    not_found_messages = {
        'en': "This information is not available in the provided document context.",
        'es': "Esta información no está disponible en el contexto del documento proporcionado.",
        'fr': "Cette information n'est pas disponible dans le contexte du document fourni.",
        'de': "Diese Information ist im bereitgestellten Dokumentkontext nicht verfügbar.",
        'hi': "यह जानकारी प्रदान किए गए दस्तावेज़ के संदर्भ में उपलब्ध नहीं है।",
        'ta': "வழங்கப்பட்ட ஆவண சூழலில் இந்த தகவல் கிடைக்கவில்லை।",
    }
    
    not_found_message = not_found_messages.get(detected_language, not_found_messages['en'])
    
    base_instruction = f"""**RESPONSE LANGUAGE: ALL ANSWERS MUST BE IN {language_name} ({detected_language})**

You are an expert document analyst with strong reasoning capabilities.

**CONTEXT:**
{{context}}

**QUESTION:** {{input}}

**ANALYSIS PROTOCOL:**
1. **UNDERSTAND THE QUESTION**: Fully comprehend what is being asked
2. **SEARCH COMPREHENSIVELY**: Look through the entire context for relevant information
3. **SYNTHESIZE AND REASON**: Connect related information and draw logical conclusions
4. **PROVIDE COMPLETE ANSWER**: Address all aspects of the question"""

    query_specific = ""
    
    if query_analysis["is_multi_part"]:
        query_specific += """
5. **MULTI-PART HANDLING**: This question has multiple parts. Address EACH part systematically."""
    
    if query_analysis["requires_procedure"]:
        query_specific += """
5. **PROCEDURAL FOCUS**: Provide clear, step-by-step instructions when available."""
    
    if query_analysis["requires_listing"]:
        query_specific += """
5. **LISTING FOCUS**: Provide comprehensive lists or enumerations as requested."""
    
    if query_analysis["requires_contact"]:
        query_specific += """
5. **CONTACT FOCUS**: Provide complete contact information including emails, phones, addresses."""
    
    if query_analysis["expected_answer_type"] == "boolean":
        query_specific += """
5. **BOOLEAN RESPONSE**: Start with "Yes" or "No" and provide supporting reasoning."""
    
    if query_analysis["expected_answer_type"] == "numerical":
        query_specific += """
5. **NUMERICAL FOCUS**: Extract exact numbers, measurements, or quantities from the context."""
    
    if query_analysis["complexity"] == "high":
        word_limit = "200"
        response_detail = "comprehensive and detailed"
    elif query_analysis["complexity"] == "medium":
        word_limit = "150"
        response_detail = "clear and complete"
    else:
        word_limit = "100"
        response_detail = "concise but complete"
    
    final_instruction = f"""

**RESPONSE REQUIREMENTS:**
- Answer must be {response_detail}
- Maximum {word_limit} words
- Use only information from the provided context
- If information is not available, respond: "{not_found_message}"
- Never mention the document or context in your response
- For mathematical questions: provide only the answer if directly available in context

**Answer in {language_name} (max {word_limit} words):**"""

    return base_instruction + query_specific + final_instruction


# --- Mission Detection and Execution ---
def detect_mission_document(doc: ProcessedDocument) -> bool:
    """Enhanced mission document detection"""
    if not doc or not doc.content:
        return False

    content_lower = doc.content.lower()

    primary_keywords = [
        "sachin's parallel world",
        "mission brief",
        "myfavouritecity",
        "getfirstcityflightnumber"
    ]

    secondary_keywords = [
        "flight number",
        "landmark",
        "city",
        "api endpoint",
        "secret token"
    ]

    url_patterns = [
        "myfavouritecity",
        "getfirstcityflightnumber",
        "flightnumber"
    ]

    primary_matches = sum(1 for keyword in primary_keywords if keyword in content_lower)
    secondary_matches = sum(1 for keyword in secondary_keywords if keyword in content_lower)
    url_matches = sum(1 for pattern in url_patterns if pattern in content_lower)

    is_mission = (
        primary_matches >= 2 or
        (primary_matches >= 1 and secondary_matches >= 3) or
        url_matches >= 2
    )

    logging.info(f"Mission detection - Primary: {primary_matches}, Secondary: {secondary_matches}, URLs: {url_matches}, Is Mission: {is_mission}")
    return is_mission


def create_mission_solving_agent_prompt(detected_language: str) -> ChatPromptTemplate:
    """Create mission-solving agent prompt with language enforcement"""
    language_name = get_language_name(detected_language).upper()

    system_message = f"""**CRITICAL: ALL RESPONSES MUST BE IN {language_name} ({detected_language}). NON-NEGOTIABLE.**

You are a mission execution specialist. Your task is to find the final flight number by following these exact steps:

**MISSION EXECUTION PROTOCOL:**
1. **STEP 1**: Locate the URL containing `myFavouriteCity` in the provided context
2. **STEP 2**: Use `fetch_contextual_url_content` tool to call that URL and get the city name
3. **STEP 3**: Find the city name in the tables/context to identify its corresponding landmark
4. **STEP 4**: Locate the URL with the landmark pattern (get...FlightNumber) in the context
5. **STEP 5**: Use `fetch_contextual_url_content` tool to call the final URL and get flight number

**OUTPUT REQUIREMENT:**
- Your final response must contain ONLY the flight number
- No additional text, explanations, or formatting
- Example: "AI101" or "6E2045" (just the flight number)
- The flight number MUST be in {language_name}"""

    # The 'agent_scratchpad' placeholder is essential for the agent to remember previous steps
    return ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("human", "Execute the mission protocol. CONTEXT:\n---\n{context}\n---"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])


@tool
async def fetch_contextual_url_content(url: str, context_hint: str = "") -> str:
    """Enhanced URL fetching with better error handling"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json,text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
        }

        response = requests.get(url, timeout=45, headers=headers)
        response.raise_for_status()

        content_type = response.headers.get('Content-Type', '').lower()

        if 'application/json' in content_type:
            try:
                json_data = response.json()
                return json.dumps(json_data, indent=2, ensure_ascii=False)
            except json.JSONDecodeError:
                return response.text
        elif 'text/html' in content_type:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove unwanted elements
            for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
                element.decompose()

            # Get clean text
            text = soup.get_text(separator=' ', strip=True)
            text = re.sub(r'\s+', ' ', text).strip()

            return text
        else:
            return response.text

    except requests.RequestException as e:
        error_msg = f"Failed to fetch URL {url}: {str(e)}"
        logging.error(error_msg)
        return error_msg
   
   
async def handle_mission_document(processed_doc: ProcessedDocument, questions: List[str], logger: logging.Logger) -> List[str]:
    """Handle mission documents with special processing"""
    try:
        tools = [fetch_contextual_url_content]
        
        # Add table tools if dataframes are available
        if processed_doc.dataframes:
            DataFrameTools.register_document(processed_doc)
            tools.extend([DataFrameTools.query_table, DataFrameTools.list_available_tables])
        
        mission_prompt = create_mission_solving_agent_prompt(processed_doc.detected_language)
        mission_agent = create_tool_calling_agent(llm, tools, mission_prompt)
        mission_executor = AgentExecutor(
            agent=mission_agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=10  # Increased for more steps
        )
        
        answers = []
        for i, question in enumerate(questions):
            if i == 0:
                # First question executes the mission
                logger.info("Executing mission agent to find flight number...")
                response = await mission_executor.ainvoke({"context": processed_doc.content})
                mission_result = response.get("output", "Mission execution failed").strip()
                
                logger.info(f"Raw mission result: {mission_result}")
                
                # More flexible flight number extraction with multiple patterns
                patterns = [
                    r'\b[A-Z0-9]{2}[\s-]?\d{3,4}\b',  # Standard format like AI101
                    r'\b[A-Z]{1,3}\d{1,4}[A-Z]?\b',    # More flexible format
                    r'\b\d{1,2}[A-Z]\d{1,4}\b',        # Format like 6E2045
                    r'Flight\s*(?:number|#)?:?\s*([A-Z0-9]{2,6})',  # With "Flight number:" prefix
                    r'Flight\s*(?:is|:)?\s*([A-Z0-9]{2,6})'         # With "Flight is:" prefix
                ]
                
                # Try all patterns
                for pattern in patterns:
                    flight_match = re.search(pattern, mission_result, re.IGNORECASE)
                    if flight_match:
                        flight_num = flight_match.group()
                        # If we matched a pattern with capturing group, use the group
                        if '(' in pattern:
                            flight_num = flight_match.group(1)
                        # Clean up the flight number
                        flight_num = re.sub(r'[^A-Z0-9]', '', flight_num.upper())
                        logger.info(f"Found flight number: {flight_num} using pattern: {pattern}")
                        answers.append(flight_num)
                        break
                else:
                    # If no pattern matched, return the raw result
                    logger.warning("Could not extract flight number, returning raw result")
                    answers.append(mission_result)
            else:
                answers.append("Mission objective completed. Refer to first answer.")
        
        return answers
        
    except Exception as e:
        logger.error(f"Mission processing failed: {e}", exc_info=True)
        return ["Mission execution failed."] * len(questions)
    
  
    
# # --- UNIVERSAL PROCESSING PIPELINE ---
# async def process_query_universal(doc_url: str, questions: List[str], logger: logging.Logger, request_id: str) -> List[str]:
#     """Universal processing pipeline that works for any domain"""
    
#     try:
#         # Document processing
#         response = requests.get(doc_url, timeout=120)
#         response.raise_for_status()
#         doc_type = await detect_document_type_http(doc_url)
        
#         processed_doc = await TargetedDocumentProcessor.process_document(
#             response.content, doc_type, doc_url, request_id
#         )
        
#         logger.info(f"Processed {doc_type} document: {len(processed_doc.content)} chars")
        
#         # Check for mission documents (keep this special case)
#         is_mission_doc = detect_mission_document(processed_doc)
        
#         if is_mission_doc:
#             return await handle_mission_document(processed_doc, questions, logger)
        
#         # Universal chunking
#         chunks = UniversalAdaptiveChunking.create_adaptive_chunks(processed_doc)
#         logger.info(f"Created {len(chunks)} adaptive chunks")
        
#         # Set up retrieval
#         embedding_model = embeddings_accurate if len(processed_doc.content) > 50000 else embeddings_fast
#         if not embedding_model:
#             embedding_model = embeddings_fast or embeddings_accurate
        
#         vectorstore = FAISS.from_documents(chunks, embedding_model)
        
#         # Register document for table tools if needed
#         if processed_doc.dataframes:
#             DataFrameTools.register_document(processed_doc)
        
#         # Process questions
#         answers = []
#         for i, question in enumerate(questions):
#             try:
#                 # Analyze query
#                 query_analysis = UniversalQueryAnalyzer.analyze_query(question)
#                 logger.info(f"Q{i+1}: {query_analysis['query_type']} query, complexity: {query_analysis['complexity']}")
                
#                 # Adaptive retrieval based on query complexity
#                 if query_analysis["complexity"] == "high" or query_analysis["is_multi_part"]:
#                     k = 15
#                 elif query_analysis["complexity"] == "medium":
#                     k = 12
#                 else:
#                     k = 8
                
#                 # Retrieve documents
#                 docs = vectorstore.similarity_search(question, k=k)
                
#                 # Apply reranking if available and beneficial
#                 if RERANK_AVAILABLE and reranker and len(docs) > 5:
#                     pairs = [(question, doc.page_content) for doc in docs]
#                     scores = reranker.predict(pairs)
#                     scored_docs = list(zip(docs, scores))
#                     scored_docs.sort(key=lambda x: x[1], reverse=True)
#                     docs = [doc for doc, _ in scored_docs[:10]]
                
#                 # Generate adaptive prompt
#                 prompt_template = generate_universal_adaptive_prompt(
#                     processed_doc.detected_language, 
#                     query_analysis
#                 )
#                 prompt = ChatPromptTemplate.from_template(prompt_template)
#                 chain = create_stuff_documents_chain(llm, prompt)
                
#                 # Generate answer
#                 result = await chain.ainvoke({"context": docs, "input": question})
                
#                 # Clean result
#                 cleaned_result = clean_and_validate_answer(result, processed_doc.detected_language)
#                 answers.append(cleaned_result)
                
#                 logger.info(f"Q{i+1}: Completed successfully")
                
#             except Exception as e:
#                 logger.error(f"Q{i+1}: Error: {e}")
#                 not_found_messages = {
#                     'en': "This information is not available in the provided document context.",
#                     'es': "Esta información no está disponible en el contexto del documento proporcionado.",
#                     'fr': "Cette information n'est pas disponible dans le contexte du document fourni.",
#                     'hi': "यह जानकारी प्रदान किए गए दस्तावेज़ के संदर्भ में उपलब्ध नहीं है।",
#                     'ta': "வழங்கப்பட்ட ஆவண சூழலில் இந்த தகவல் கிடைக்கவில்லை।",
#                 }
#                 answers.append(not_found_messages.get(processed_doc.detected_language, "Processing failed."))
        
#         return answers
        
#     except Exception as e:
#         logger.error(f"Processing failed: {e}")
#         return ["Processing failed."] * len(questions)

# 2. Modify your process_query_universal function to use the async logger:
async def process_query_universal(doc_url: str, questions: List[str], logger: logging.Logger, request_id: str) -> List[str]:
    """Universal processing pipeline that works for any domain"""
    
    try:
        start_time = asyncio.get_event_loop().time()
        
        # Document processing
        response = requests.get(doc_url, timeout=120)
        response.raise_for_status()
        doc_type = await detect_document_type_http(doc_url)
        
        # Log the document asynchronously (this won't block)
        log_document_async(response.content, doc_url, doc_type, request_id)
        
        # Log questions asynchronously (this won't block)
        log_questions_async(questions, doc_url, request_id)
        
        processed_doc = await TargetedDocumentProcessor.process_document(
            response.content, doc_type, doc_url, request_id
        )
        
        logger.info(f"Processed {doc_type} document: {len(processed_doc.content)} chars")
        
        # Rest of your existing code...
        # [...]
        
        # Process questions
        answers = []
        # [Your existing code to process questions]
        
        # Calculate processing time
        end_time = asyncio.get_event_loop().time()
        processing_time = end_time - start_time
        
        # Log answers asynchronously (this won't block)
        metrics = {
            "document_size": len(processed_doc.content),
            "document_type": doc_type,
            "language": processed_doc.detected_language,
            "chunk_count": len(chunks) if 'chunks' in locals() else 0
        }
        log_answers_async(questions, answers, doc_url, request_id, processing_time, metrics)
        
        return answers
        
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        return ["Processing failed."] * len(questions)

            
def clean_and_validate_answer(result: str, detected_language: str) -> str:
    """Clean and validate answer, ensuring language consistency"""
    if not result or len(result.strip()) < 3:
        not_found_messages = {
            'en': "This information is not available in the provided document context.",
            'es': "Esta información no está disponible en el contexto del documento proporcionado.",
            'fr': "Cette information n'est pas disponible dans le contexte du document fourni.",
            'de': "Diese Information ist im bereitgestellten Dokumentkontext nicht verfügbar.",
            'it': "Questa informazione non è disponibile nel contesto del documento fornito.",
            'hi': "यह जानकारी प्रदान किए गए दस्तावेज़ के संदर्भ में उपलब्ध नहीं है।",
            'bn': "প্রদত্ত নথির প্রেক্ষাপটে এই তথ্য উপলব্ধ নয়।",
            'te': "సమర్పించిన పత్రం సందర్భంలో ఈ సమాచారం అందుబాటులో లేదు।",
            'ta': "வழங்கப்பட்ட ஆவண சூழலில் இந்த தகவல் கিடைக்கவில்லை।",
            'mr': "दिलेल्या दस्तऐवजाच्या संदर्भात ही माहिती उपलब्ध नाही।",
        }
        return not_found_messages.get(detected_language, not_found_messages['en'])

    answer = result.strip()

    # Remove common AI-generated prefixes for English
    if detected_language == "en":
        prefixes_to_remove = [
            r'^Based on the (?:enhanced )?context(?:,?)\s*',
            r'^According to the (?:provided )?(?:enhanced )?(?:context|document)(?:,?)\s*',
            r'^The (?:enhanced )?context (?:shows|indicates) that\s*',
            r'^From the (?:provided )?(?:enhanced )?(?:context|sources)(?:,?)\s*'
        ]
        for prefix_pattern in prefixes_to_remove:
            answer = re.sub(prefix_pattern, '', answer, flags=re.IGNORECASE)

    # Clean up whitespace
    answer = re.sub(r'\s+', ' ', answer).strip()

    # Enforce word limit based on complexity (handled in prompt generation)
    words = answer.split()
    if len(words) > 200:  # Max absolute limit
        sentences = re.split(r'[.!?।？！]', answer)
        truncated_sentences = []
        word_count = 0

        for sentence in sentences:
            sentence_words = sentence.strip().split()
            if word_count + len(sentence_words) <= 200:
                truncated_sentences.append(sentence.strip())
                word_count += len(sentence_words)
            else:
                break

        if truncated_sentences:
            answer = '. '.join(truncated_sentences)
            if not answer.endswith(('.', '!', '?', '।', '？', '！')):
                answer += '.'
        else:
            answer = ' '.join(words[:200]) + '...'

    # Add proper ending punctuation based on language
    if answer and not answer.endswith(('.', '!', '?', '।', '？', '！', '...')):
        if detected_language in ['hi', 'bn', 'te', 'ta', 'mr', 'gu']:
            answer += '।'
        else:
            answer += '.'

    # Capitalize first letter for Latin-script languages
    if answer and detected_language in ['en', 'es', 'fr', 'de', 'it', 'pt'] and answer[0].islower():
        answer = answer[0].upper() + answer[1:]

    return answer

