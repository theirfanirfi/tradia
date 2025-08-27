import asyncio
import aiohttp
import numpy as np
import pickle
import os
import hashlib
from typing import Dict, List, Tuple, Optional
from fastapi import HTTPException
from pydantic import BaseModel
import json
from sklearn.metrics.pairwise import cosine_similarity

# Configuration
OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "mxbai-embed-large:latest"
EMBEDDINGS_DIR = "embeddings_cache"
EMBEDDINGS_FILE = os.path.join(EMBEDDINGS_DIR, "section_embeddings.pkl")
SECTIONS_HASH_FILE = os.path.join(EMBEDDINGS_DIR, "sections_hash.txt")

# Section mapping
SECTION_MAP = {
    "Animals": "I",
    "Vegetables": "II",
    "Oils/Fats": "III",
    "Food/Drink": "IV",
    "Minerals": "V",
    "Chemicals": "VI",
    "Plastics/Rubber": "VII",
    "Leather/Furs": "VIII",
    "Woodwork": "IX",
    "Paper": "X",
    "Textiles": "XI",
    "Footwear/Wearables": "XII",
    "Stone/Ceramics": "XIII",
    "Jewellery": "XIV",
    "Metals": "XV",
    "Machinery/Electronics": "XVI",
    "Transport": "XVII",
    "Instruments": "XVIII",
    "Arms": "XIX",
    "Misc. Goods": "XX",
    "Art/Antiques": "XXI",
}

# Request/Response models
class ClassificationRequest(BaseModel):
    text: str

class ClassificationResponse(BaseModel):
    predicted_section: str
    section_code: str
    confidence_score: float
    all_scores: Dict[str, float]

class OllamaClassifier:
    def __init__(self):
        self.section_embeddings: Optional[Dict[str, np.ndarray]] = None
        self.section_names = list(SECTION_MAP.keys())
        # Create embeddings directory if it doesn't exist
        os.makedirs(EMBEDDINGS_DIR, exist_ok=True)
    
    def _get_sections_hash(self) -> str:
        """Generate a hash of the section names to detect changes"""
        sections_str = json.dumps(sorted(self.section_names))
        return hashlib.md5(sections_str.encode()).hexdigest()
    
    def _save_embeddings_to_file(self):
        """Save embeddings and sections hash to files"""
        try:
            # Save embeddings
            with open(EMBEDDINGS_FILE, 'wb') as f:
                pickle.dump(self.section_embeddings, f)
            
            # Save sections hash
            with open(SECTIONS_HASH_FILE, 'w') as f:
                f.write(self._get_sections_hash())
            
            print(f"Embeddings saved to {EMBEDDINGS_FILE}")
        except Exception as e:
            print(f"Warning: Failed to save embeddings to file: {e}")
    
    def _load_embeddings_from_file(self) -> bool:
        """Load embeddings from file if they exist and are valid"""
        try:
            # Check if files exist
            if not (os.path.exists(EMBEDDINGS_FILE) and os.path.exists(SECTIONS_HASH_FILE)):
                print("Embedding files not found.")
                return False
            
            # Check if sections have changed
            with open(SECTIONS_HASH_FILE, 'r') as f:
                stored_hash = f.read().strip()
            
            current_hash = self._get_sections_hash()
            if stored_hash != current_hash:
                print("Section definitions have changed. Need to regenerate embeddings.")
                return False
            
            # Load embeddings
            with open(EMBEDDINGS_FILE, 'rb') as f:
                self.section_embeddings = pickle.load(f)
            
            # Validate loaded embeddings
            if not isinstance(self.section_embeddings, dict):
                print("Invalid embeddings format in file.")
                return False
            
            # Check if all sections are present
            if set(self.section_embeddings.keys()) != set(self.section_names):
                print("Cached embeddings don't match current sections.")
                return False
            
            print(f"Successfully loaded embeddings from {EMBEDDINGS_FILE}")
            return True
            
        except Exception as e:
            print(f"Error loading embeddings from file: {e}")
            return False
    
    async def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding from Ollama API"""
        url = f"{OLLAMA_BASE_URL}/api/embeddings"
        payload = {
            "model": MODEL_NAME,
            "prompt": text
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        raise HTTPException(
                            status_code=500, 
                            detail=f"Ollama API error: {response.status}"
                        )
                    
                    data = await response.json()
                    embedding = np.array(data["embedding"])
                    return embedding
                    
            except aiohttp.ClientError as e:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Failed to connect to Ollama: {str(e)}"
                )
    
    async def initialize_embeddings(self):
        """Load embeddings from file or generate new ones if needed"""
        if self.section_embeddings is not None:
            return
        
        print("Initializing section embeddings...")
        
        # Try to load from file first
        if self._load_embeddings_from_file():
            print("Using cached embeddings.")
            return
        
        # Generate new embeddings if loading failed
        print("Generating new embeddings...")
        self.section_embeddings = {}
        
        for i, section_name in enumerate(self.section_names, 1):
            print(f"Processing section {i}/{len(self.section_names)}: {section_name}")
            
            # Create descriptive text for better embeddings
            descriptive_text = f"{section_name} products and goods"
            embedding = await self.get_embedding(descriptive_text)
            self.section_embeddings[section_name] = embedding
        
        # Save embeddings to file for future use
        self._save_embeddings_to_file()
        print("Section embeddings initialized and saved successfully!")
    
    async def classify(self, text: str) -> ClassificationResponse:
        """Classify input text into one of the sections"""
        # Ensure embeddings are initialized
        await self.initialize_embeddings()
        
        # Get embedding for input text
        input_embedding = await self.get_embedding(text)
        
        # Calculate cosine similarities
        similarities = {}
        for section_name, section_embedding in self.section_embeddings.items():
            # Reshape for sklearn cosine_similarity
            input_emb_2d = input_embedding.reshape(1, -1)
            section_emb_2d = section_embedding.reshape(1, -1)
            
            similarity = cosine_similarity(input_emb_2d, section_emb_2d)[0][0]
            similarities[section_name] = float(similarity)
        
        # Find the section with highest similarity
        best_section = max(similarities, key=similarities.get)
        best_score = similarities[best_section]
        
        return ClassificationResponse(
            predicted_section=best_section,
            section_code=SECTION_MAP[best_section],
            confidence_score=best_score,
            all_scores=similarities
        )

# Initialize classifier
classifier = OllamaClassifier()

# Example usage and testing
if __name__ == "__main__":

    
    # Example test function
    async def test_classifier():
        test_inputs = [
            "leather shoes",
            "gold necklace", 
            "wooden table",
            "steel pipes",
            "cotton fabric",
            "olive oil",
            "smartphone",
            "car engine"
        ]
        
        for text in test_inputs:
            try:
                result = await classifier.classify(text)
                print(f"\nInput: '{text}'")
                print(f"Predicted: {result.predicted_section} ({result.section_code})")
                print(f"Confidence: {result.confidence_score:.4f}")
                print("Top 3 matches:")
                sorted_scores = sorted(result.all_scores.items(), 
                                     key=lambda x: x[1], reverse=True)[:3]
                for section, score in sorted_scores:
                    print(f"  {section}: {score:.4f}")
            except Exception as e:
                print(f"Error classifying '{text}': {e}")
    

    asyncio.run(test_classifier())
