import asyncio
import logging
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any

# Import from separate modules
from tools.get_page_content import get_page_content
from tools.extract_vocabulary import extract_vocabulary
from tools.save_results import save_results
from tools.generate_song_id import generate_song_id

# Configure logging
logger = logging.getLogger(__name__)

async def process_song_url(url: str, lyrics_path: Path, vocabulary_path: Path) -> Optional[str]:
    """
    Process a French song URL by extracting lyrics, parsing vocabulary, and saving results.
    
    Args:
        url (str): URL of the song lyrics page
        lyrics_path (Path): Directory to save lyrics files
        vocabulary_path (Path): Directory to save vocabulary files
        
    Returns:
        Optional[str]: The song_id if successful, None otherwise
    """
    # Create directories if they don't exist
    lyrics_path.mkdir(parents=True, exist_ok=True)
    vocabulary_path.mkdir(parents=True, exist_ok=True)
    
    # Extract lyrics from the URL
    result = await get_page_content(url)
    
    if not result["french_lyrics"]:
        logger.error(f"Failed to extract lyrics from {url}: {result['metadata']}")
        return None
    
    # Generate a song ID from artist and title if available
    if result.get("artist") and result.get("title"):
        song_id_result = generate_song_id(result["artist"], result["title"])
        song_id = song_id_result["song_id"]
        logger.info(f"Generated song ID: {song_id}")
    else:
        # Fallback to UUID if artist or title not found
        song_id = str(uuid.uuid4())[:8]
        logger.info(f"Using fallback song ID: {song_id}")
    
    # Extract vocabulary using the LLM approach
    try:
        vocabulary = await extract_vocabulary(result["french_lyrics"])
        logger.info(f"Successfully extracted {len(vocabulary)} vocabulary items")
    except Exception as e:
        logger.error(f"Failed to extract vocabulary with LLM, using fallback method: {str(e)}")
        # If LLM extraction fails, use the basic parser as fallback
        from tools.get_page_content import parse_lyrics_to_db_format
        vocab_dict = parse_lyrics_to_db_format(result["french_lyrics"])
        
        # Convert to flat format
        vocabulary = []
        
        # Add nouns
        for noun in vocab_dict["nouns"]:
            noun_entry = noun.copy()
            noun_entry["type"] = "noun"
            vocabulary.append(noun_entry)
        
        # Add verbs
        for verb in vocab_dict["verbs"]:
            verb_entry = verb.copy()
            verb_entry["type"] = "verb"
            vocabulary.append(verb_entry)
        
        # Add adjectives
        for adj in vocab_dict["adjectives"]:
            adj_entry = adj.copy()
            adj_entry["type"] = "adjective"
            vocabulary.append(adj_entry)
            
        logger.info(f"Fallback parsing extracted {len(vocabulary)} vocabulary items")
    
    # Save results
    save_results(song_id, result["french_lyrics"], vocabulary, lyrics_path, vocabulary_path)
    
    logger.info(f"Successfully processed song: {song_id}")
    return song_id

async def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Define paths
    base_path = Path("./data")
    lyrics_path = base_path / "lyrics"
    vocabulary_path = base_path / "vocabulary"
    
    # Example URL (replace with actual French lyrics URL)
    url = "https://example.com/french-song-lyrics"
    
    # Process the song
    song_id = await process_song_url(url, lyrics_path, vocabulary_path)
    
    if song_id:
        print(f"Song processed successfully. ID: {song_id}")
    else:
        print("Failed to process song")

if __name__ == "__main__":
    asyncio.run(main())