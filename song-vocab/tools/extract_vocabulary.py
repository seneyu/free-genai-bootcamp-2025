from typing import List, Dict, Any
import instructor
import ollama
import logging
from pydantic import BaseModel, Field
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

class PresentTense(BaseModel):
    je: str = ""
    tu: str = ""
    il_elle: str = Field("", alias="il/elle")
    nous: str = ""
    vous: str = ""
    ils_elles: str = Field("", alias="ils/elles")

class PastParticiple(BaseModel):
    masculine_singular: str = ""
    feminine_singular: str = ""
    masculine_plural: str = ""
    feminine_plural: str = ""

class VerbParts(BaseModel):
    infinitive: str
    present: PresentTense
    past_participle: PastParticiple

class AdjectiveParts(BaseModel):
    masculine: str
    feminine: str
    masculine_plural: str
    feminine_plural: str

class NounParts(BaseModel):
    definite_article: str = ""
    indefinite_article: str = ""
    plural: str

class Verb(BaseModel):
    french: str
    english: str
    type: str = "verb"
    parts: VerbParts

class Adjective(BaseModel):
    french: str
    english: str
    type: str = "adjective"
    parts: AdjectiveParts

class Noun(BaseModel):
    french: str
    english: str
    type: str = "noun"
    gender: str
    parts: NounParts

class FrenchVocabularyResponse(BaseModel):
    verbs: List[Verb] = []
    adjectives: List[Adjective] = []
    nouns: List[Noun] = []

async def extract_vocabulary(text: str) -> List[Dict[str, Any]]:
    """
    Extract vocabulary from French text using LLM with structured output.
    
    Args:
        text (str): The text to extract vocabulary from
        
    Returns:
        List[Dict[str, Any]]: Complete list of vocabulary items in French format
    """
    logger.info("Starting French vocabulary extraction")
    logger.debug(f"Input text length: {len(text)} characters")
    
    try:
        # Initialize Ollama client with instructor
        logger.debug("Initializing Ollama client with instructor")
        client = instructor.patch(ollama.Client())
        
        # Load the prompt from the prompts directory
        prompt_path = Path(__file__).parent.parent / "prompts" / "Extract-French-Vocabulary.md"
        logger.debug(f"Loading prompt from {prompt_path}")
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt_template = f.read()
        
        # Construct the full prompt with the text to analyze
        prompt = f"{prompt_template}\n\nText to analyze:\n{text}"
        logger.debug(f"Constructed prompt of length {len(prompt)}")
        
        # We'll use multiple calls to ensure we get all vocabulary
        all_vocabulary = []
        max_attempts = 3
        
        for attempt in range(max_attempts):
            logger.info(f"Making LLM call attempt {attempt + 1}/{max_attempts}")
            try:
                response = await client.chat(
                    model="mistral",
                    messages=[{"role": "user", "content": prompt}],
                    response_model=FrenchVocabularyResponse
                )
                
                # Process verbs
                for verb in response.verbs:
                    verb_dict = verb.dict(by_alias=True)
                    all_vocabulary.append(verb_dict)
                
                # Process adjectives
                for adj in response.adjectives:
                    adj_dict = adj.dict(by_alias=True)
                    all_vocabulary.append(adj_dict)
                
                # Process nouns
                for noun in response.nouns:
                    noun_dict = noun.dict(by_alias=True)
                    all_vocabulary.append(noun_dict)
                
                logger.info(f"Attempt {attempt + 1} added {len(response.verbs) + len(response.adjectives) + len(response.nouns)} items")
                
                # If we got a reasonable number of items, we can stop
                if len(all_vocabulary) > 10:
                    break
                
            except Exception as e:
                logger.error(f"Error in attempt {attempt + 1}: {str(e)}")
                if attempt == max_attempts - 1:
                    raise  # Re-raise on last attempt
        
        logger.info(f"Extracted {len(all_vocabulary)} unique vocabulary items")
        return all_vocabulary
        
    except Exception as e:
        logger.error(f"Failed to extract vocabulary: {str(e)}", exc_info=True)
        raise

# Example of expected extract-french-vocabulary.md prompt content:
"""
You are a French language expert. Your task is to identify and extract vocabulary from French text.

For each word, determine its part of speech (verb, adjective, or noun) and provide the following information:

For verbs:
- The infinitive form
- Present tense conjugations (je, tu, il/elle, nous, vous, ils/elles)
- Past participle forms (masculine/feminine singular/plural)

For adjectives:
- Base form
- Gender forms (masculine, feminine, masculine plural, feminine plural)

For nouns:
- Base form
- Gender (masculine or feminine)
- Appropriate definite and indefinite articles
- Plural form

Please analyze the text carefully and extract all important vocabulary items.

Provide your response in a structured format.
"""