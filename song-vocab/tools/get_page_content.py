import aiohttp
from bs4 import BeautifulSoup
from typing import Dict, Optional
import re
import logging

# Configure logging
logger = logging.getLogger(__name__)

async def get_page_content(url: str) -> Dict[str, Optional[str]]:
    """
    Extract French lyrics content from a webpage.
    
    Args:
        url (str): URL of the webpage to extract content from
        
    Returns:
        Dict[str, Optional[str]]: Dictionary containing french_lyrics and metadata
    """
    logger.info(f"Fetching content from URL: {url}")
    try:
        async with aiohttp.ClientSession() as session:
            logger.debug("Making HTTP request...")
            async with session.get(url) as response:
                if response.status != 200:
                    error_msg = f"Error: HTTP {response.status}"
                    logger.error(error_msg)
                    return {
                        "french_lyrics": None,
                        "metadata": error_msg
                    }
                
                logger.debug("Reading response content...")
                html = await response.text()
                logger.info(f"Successfully fetched page content ({len(html)} bytes)")
                return extract_lyrics_from_html(html, url)
    except Exception as e:
        error_msg = f"Error fetching page: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "french_lyrics": None,
            "metadata": error_msg
        }

def extract_lyrics_from_html(html: str, url: str) -> Dict[str, Optional[str]]:
    """
    Extract French lyrics from HTML content based on common patterns in lyrics websites.
    """
    logger.info("Starting French lyrics extraction from HTML")
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove script and style elements
    logger.debug("Cleaning HTML content...")
    for element in soup(['script', 'style', 'header', 'footer', 'nav']):
        element.decompose()
    
    # Common patterns for lyrics containers
    lyrics_patterns = [
        # Class patterns
        {"class_": re.compile(r"lyrics?|paroles?|texte", re.I)},
        {"class_": re.compile(r"song-content|song-text|track-text|chanson", re.I)},
        # ID patterns
        {"id": re.compile(r"lyrics?|paroles?|texte", re.I)},
        # Common French lyrics sites patterns
        {"class_": "lyrics_box"},
        {"class_": "paroles_box"},
        {"class_": "lyrics-content"}
    ]
    
    french_lyrics = None
    artist = None
    title = None
    metadata = ""
    
    # Try to find lyrics containers
    logger.debug("Searching for lyrics containers...")
    for pattern in lyrics_patterns:
        logger.debug(f"Trying pattern: {pattern}")
        elements = soup.find_all(**pattern)
        logger.debug(f"Found {len(elements)} matching elements")
        
        for element in elements:
            text = clean_text(element.get_text())
            logger.debug(f"Extracted text length: {len(text)} chars")
            
            # Detect if text is primarily French
            if is_primarily_french(text) and not french_lyrics:
                logger.info("Found French lyrics")
                french_lyrics = text
    
    # If no structured containers found, try to find the largest text block
    if not french_lyrics:
        logger.info("No lyrics found in structured containers, trying fallback method")
        text_blocks = [clean_text(p.get_text()) for p in soup.find_all('p')]
        if text_blocks:
            largest_block = max(text_blocks, key=len)
            logger.debug(f"Found largest text block: {len(largest_block)} chars")
            
            if is_primarily_french(largest_block):
                logger.info("Largest block contains French text")
                french_lyrics = largest_block
    
    # Extract metadata (title, artist) if available
    try:
        # Try to find the title from common patterns
        title_patterns = [
            {"class_": re.compile(r"title|song-name|track-title", re.I)},
            {"id": re.compile(r"title|song-name|track-title", re.I)}
        ]
        
        for pattern in title_patterns:
            title_element = soup.find(**pattern)
            if title_element:
                title = clean_text(title_element.get_text())
                break
                
        # Try to find the artist from common patterns
        artist_patterns = [
            {"class_": re.compile(r"artist|singer|author", re.I)},
            {"id": re.compile(r"artist|singer|author", re.I)}
        ]
        
        for pattern in artist_patterns:
            artist_element = soup.find(**pattern)
            if artist_element:
                artist = clean_text(artist_element.get_text())
                break
                
        # If we couldn't find them with patterns, try the page title
        if not title or not artist:
            page_title = soup.find('title')
            if page_title:
                page_title_text = page_title.get_text().strip()
                # Common format: "Title - Artist | Lyrics"
                title_parts = page_title_text.split('-', 1)
                if len(title_parts) > 1:
                    if not title:
                        title = title_parts[0].strip()
                    if not artist:
                        # Remove common suffixes like "| Lyrics"
                        artist_part = title_parts[1].split('|')[0].strip()
                        artist = artist_part
        
        metadata = f"Title: {title or 'Unknown'}, Artist: {artist or 'Unknown'}"
        logger.debug(f"Found metadata: {metadata}")
        
    except Exception as e:
        logger.error(f"Error extracting metadata: {str(e)}")
        metadata = "Lyrics extracted successfully"

    result = {
        "french_lyrics": french_lyrics,
        "metadata": metadata,
        "title": title,
        "artist": artist
    }
    
    # Log the results
    if french_lyrics:
        logger.info(f"Found French lyrics ({len(french_lyrics)} chars)")
    
    return result

def clean_text(text: str) -> str:
    """
    Clean extracted text by removing extra whitespace and unnecessary characters.
    """
    logger.debug(f"Cleaning text of length {len(text)}")
    # Remove HTML entities
    text = re.sub(r'&[a-zA-Z]+;', ' ', text)
    # Remove multiple spaces and newlines
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n', text)
    # Remove leading/trailing whitespace
    result = text.strip()
    logger.debug(f"Text cleaned, new length: {len(result)}")
    return result

def is_primarily_french(text: str) -> bool:
    """
    Check if text contains primarily French characters and patterns.
    """
    # Count French-specific characters and patterns
    french_chars = len(re.findall(r'[éèêëàâäôöùûüçÉÈÊËÀÂÄÔÖÙÛÜÇ]', text))
    
    # Look for common French words
    common_french_words = [
        r'\ble\b', r'\bla\b', r'\bles\b', r'\bun\b', r'\bune\b', r'\bdes\b',
        r'\bet\b', r'\bou\b', r'\bje\b', r'\btu\b', r'\bil\b', r'\belle\b',
        r'\bnous\b', r'\bvous\b', r'\bils\b', r'\belles\b', r'\bsuis\b',
        r'\best\b', r'\bsommes\b', r'\bêtes\b', r'\bsont\b', r'\bdans\b',
        r'\bpour\b', r'\bavec\b', r'\bsur\b', r'\bau\b', r'\baux\b'
    ]
    
    french_words_count = sum(len(re.findall(pattern, text, re.IGNORECASE)) for pattern in common_french_words)
    
    # Calculate weight
    total_chars = len(text.strip())
    total_words = len(text.split())
    
    if total_chars == 0 or total_words == 0:
        return False
    
    # Weight French character ratio and common word ratio
    char_ratio = french_chars / total_chars
    word_ratio = french_words_count / total_words
    
    logger.debug(f"French character ratio: {char_ratio:.2f} ({french_chars}/{total_chars})")
    logger.debug(f"French word ratio: {word_ratio:.2f} ({french_words_count}/{total_words})")
    
    # Combined score with more weight on word patterns
    score = (char_ratio * 0.3) + (word_ratio * 0.7)
    
    return score > 0.15  # Lower threshold to catch more French text

def parse_lyrics_to_db_format(lyrics: str) -> Dict:
    """
    Parse French lyrics to identify words and their parts of speech
    for database storage. This is a basic implementation that would need
    to be expanded with a proper French language parser.
    
    Args:
        lyrics (str): French lyrics text
        
    Returns:
        Dict: Words categorized by part of speech
    """
    logger.info("Parsing lyrics for database storage")
    
    # Basic cleaning
    clean_lyrics = re.sub(r'[^\w\s\'\-àâäæçéèêëîïôœùûüÿÀÂÄÆÇÉÈÊËÎÏÔŒÙÛÜŸ]', ' ', lyrics)
    words = re.findall(r'\b[\w\'\-àâäæçéèêëîïôœùûüÿÀÂÄÆÇÉÈÊËÎÏÔŒÙÛÜŸ]+\b', clean_lyrics.lower())
    
    # This is a placeholder for actual NLP processing
    # In a real implementation, you would use a French NLP library
    # such as spaCy with a French model or similar
    
    result = {
        "nouns": [],
        "verbs": [],
        "adjectives": []
    }
    
    # This is very simplistic and should be replaced with proper NLP
    for word in set(words):
        # Just some very basic rules as an example
        if word.endswith(('er', 'ir', 're')):
            # Possible verb
            result["verbs"].append({
                "french": word,
                "english": "",  # Would need translation service
                "parts": {
                    "infinitive": word,
                    "present": {
                        "je": "",
                        "tu": "",
                        "il/elle": "",
                        "nous": "",
                        "vous": "",
                        "ils/elles": ""
                    },
                    "past_participle": {
                        "masculine_singular": "",
                        "feminine_singular": "",
                        "masculine_plural": "",
                        "feminine_plural": ""
                    }
                }
            })
        elif word.endswith(('e', 'es', 's')):
            # Possible adjective or noun
            base_form = word.rstrip('es')
            result["adjectives"].append({
                "french": base_form,
                "english": "",  # Would need translation service
                "parts": {
                    "masculine": base_form,
                    "feminine": base_form + "e" if not word.endswith('e') else base_form,
                    "masculine_plural": base_form + "s" if not word.endswith('s') else base_form,
                    "feminine_plural": base_form + "es" if not word.endswith('es') else base_form
                }
            })
        else:
            # Default to noun
            result["nouns"].append({
                "french": word,
                "english": "",  # Would need translation service
                "gender": "",  # Would need dictionary lookup
                "parts": {
                    "definite_article": "",
                    "indefinite_article": "",
                    "plural": word + "s" if not word.endswith('s') else word
                }
            })
    
    logger.info(f"Parsed {len(result['nouns'])} nouns, {len(result['verbs'])} verbs, and {len(result['adjectives'])} adjectives")
    return result