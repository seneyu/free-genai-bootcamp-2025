import chromadb
from chromadb.utils import embedding_functions
import json
import os
import boto3
from typing import Dict, List, Optional
import re

class BedrockEmbeddingFunction(embedding_functions.EmbeddingFunction):
    def __init__(self, model_id="amazon.titan-embed-text-v1"):
        """Initialize Bedrock embedding function"""
        self.bedrock_client = boto3.client('bedrock-runtime', region_name="us-east-1")
        self.model_id = model_id

    def __call__(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts using Bedrock"""
        embeddings = []
        for text in texts:
            try:
                response = self.bedrock_client.invoke_model(
                    modelId=self.model_id,
                    body=json.dumps({
                        "inputText": text
                    })
                )
                response_body = json.loads(response['body'].read())
                embedding = response_body['embedding']
                embeddings.append(embedding)
            except Exception as e:
                print(f"Error generating embedding: {str(e)}")
                # Return a zero vector as fallback
                embeddings.append([0.0] * 1536)  # Titan model uses 1536 dimensions
        return embeddings

class FrenchQuestionVectorStore:
    def __init__(self, persist_directory: str = "data/vectorstore"):
        """Initialize the vector store for French listening questions"""
        self.persist_directory = persist_directory
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Use Bedrock's Titan embedding model
        self.embedding_fn = BedrockEmbeddingFunction()
        
        # Create or get collection for French listening questions
        self.collection = self.client.get_or_create_collection(
            name="french_listening_questions",
            embedding_function=self.embedding_fn,
            metadata={"description": "DELF French listening comprehension questions"}
        )

    def add_questions(self, questions: List[Dict], file_id: str):
        """Add questions to the vector store"""
        ids = []
        documents = []
        metadatas = []
        
        for idx, question in enumerate(questions):
            # Create a unique ID for each question
            question_id = f"{file_id}_{idx}"
            ids.append(question_id)
            
            # Store the full question structure as metadata
            metadatas.append({
                "file_id": file_id,
                "question_index": idx,
                "full_structure": json.dumps(question)
            })
            
            # Create a searchable document from the question content
            document = f"""
            Introduction: {question.get('introduction', '')}
            Conversation: {question.get('conversation', '')}
            Questions: {question.get('questions', '')}
            """
            documents.append(document)
        
        # Add to collection
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        
        print(f"Added {len(questions)} questions from file {file_id}")

    def search_similar_questions(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search for similar questions in the vector store"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # Convert results to more usable format
        questions = []
        for idx, metadata in enumerate(results['metadatas'][0]):
            question_data = json.loads(metadata['full_structure'])
            question_data['similarity_score'] = results['distances'][0][idx] if 'distances' in results else None
            question_data['file_id'] = metadata['file_id']
            questions.append(question_data)
            
        return questions

    def get_question_by_id(self, question_id: str) -> Optional[Dict]:
        """Retrieve a specific question by its ID"""
        result = self.collection.get(
            ids=[question_id],
            include=['metadatas']
        )
        
        if result['metadatas']:
            return json.loads(result['metadatas'][0]['full_structure'])
        return None

    def parse_questions_from_file(self, filename: str) -> List[Dict]:
        """Parse questions from a structured text file"""
        questions = []
        current_question = {}
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                # Skip empty lines
                if not line:
                    i += 1
                    continue
                
                # Start of a new question section
                if line == "Introduction:":
                    # Save previous question if it exists
                    if current_question and all(k in current_question for k in ["introduction", "conversation", "questions"]):
                        questions.append(current_question)
                    
                    # Start new question
                    current_question = {}
                    i += 1
                    
                    # Get introduction
                    intro_lines = []
                    while i < len(lines) and not lines[i].strip() == "Conversation:":
                        if lines[i].strip():
                            intro_lines.append(lines[i].strip())
                        i += 1
                    current_question["introduction"] = " ".join(intro_lines)
                    
                    # Get conversation
                    conv_lines = []
                    i += 1  # Skip "Conversation:" line
                    while i < len(lines) and not lines[i].strip() == "Questions:":
                        if lines[i].strip():
                            conv_lines.append(lines[i].strip())
                        i += 1
                    current_question["conversation"] = " ".join(conv_lines)
                    
                    # Get questions
                    quest_lines = []
                    i += 1  # Skip "Questions:" line
                    while i < len(lines) and not lines[i].strip().startswith("--"):
                        if lines[i].strip():
                            quest_lines.append(lines[i].strip())
                        i += 1
                    current_question["questions"] = "\n".join(quest_lines)
                
                i += 1
            
            # Don't forget to add the last question
            if current_question and all(k in current_question for k in ["introduction", "conversation", "questions"]):
                questions.append(current_question)
            
            if not questions:
                print(f"No valid questions found in {filename}")
            else:
                print(f"Successfully parsed {len(questions)} questions from {filename}")
            
            return questions
        
        except Exception as e:
            print(f"Error parsing questions from {filename}: {str(e)}")
            return []

    def index_questions_file(self, filename: str):
        """Index all questions from a file into the vector store"""
        # Extract file ID from filename (without extension)
        file_id = os.path.basename(filename).split('.')[0]
        
        # Parse questions from file
        questions = self.parse_questions_from_file(filename)
        
        # Add to vector store
        if questions:
            self.add_questions(questions, file_id)
            print(f"Indexed {len(questions)} questions from {filename}")
        else:
            print(f"No valid questions found in {filename}")

    def index_questions_directory(self, directory: str):
        """Index all question files in a directory"""
        if not os.path.exists(directory):
            print(f"Directory {directory} does not exist")
            return
        
        file_count = 0
        for filename in os.listdir(directory):
            if filename.endswith(".txt"):
                full_path = os.path.join(directory, filename)
                self.index_questions_file(full_path)
                file_count += 1
        
        print(f"Indexed questions from {file_count} files in {directory}")

if __name__ == "__main__":
    # Example usage
    store = FrenchQuestionVectorStore()
    
    # Index questions from the data/questions directory
    store.index_questions_directory("data/questions")
    
    # Example search query
    similar = store.search_similar_questions("Quel est le numéro du train qui part?", n_results=3)
    
    # Print results
    for i, result in enumerate(similar):
        print(f"\nResult {i+1}:")
        print(f"Introduction: {result.get('introduction', '')}")
        print(f"Questions: {result.get('questions', '')}")
        print(f"Similarity score: {result.get('similarity_score', 'N/A')}")