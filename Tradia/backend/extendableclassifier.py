import asyncio
import aiohttp
import numpy as np
import pickle
import os
import hashlib
import json
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
from sklearn.metrics.pairwise import cosine_similarity

# Configuration
OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "mxbai-embed-large:latest"
EMBEDDINGS_BASE_DIR = "embeddings_cache"

class ClassificationLevel(str, Enum):
    
    def save_mappings_to_file(self, filepath: str):
        """Save current mappings to JSON file"""
        try:
            data = {
                'sections': self._section_map,
                'hierarchical_mappings': self._hierarchical_mappings
            }
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Mappings saved to {filepath}")
        except Exception as e:
            print(f"Error saving mappings: {e}")
    
    def add_section(self, section_name: str, section_code: str):
        """Add a new section"""
        self._section_map[section_name] = section_code
        if section_code not in self._hierarchical_mappings:
            self._hierarchical_mappings[section_code] = {"chapters": {}}
    
    def add_chapter(self, section_code: str, chapter_name: str, chapter_code: str):
        """Add a new chapter to a section"""
        if section_code not in self._hierarchical_mappings:
            self._hierarchical_mappings[section_code] = {"chapters": {}}
        
        self._hierarchical_mappings[section_code]["chapters"][chapter_name] = chapter_code
        
        # Initialize chapter structure if it doesn't exist
        if chapter_code not in self._hierarchical_mappings[section_code]:
            self._hierarchical_mappings[section_code][chapter_code] = {"headings": {}}
    
    def add_heading(self, section_code: str, chapter_code: str, heading_name: str, heading_code: str):
        """Add a new heading to a chapter"""
        chapter_path = self._hierarchical_mappings[section_code][chapter_code]
        chapter_path["headings"][heading_name] = heading_code
        
        # Initialize heading structure if it doesn't exist
        if heading_code not in chapter_path:
            chapter_path[heading_code] = {"sub_headings": {}}
    
    def add_sub_heading(self, section_code: str, chapter_code: str, heading_code: str, 
                       sub_heading_code: str, sub_heading_name: str):
        """Add a new sub-heading to a heading"""
        heading_path = self._hierarchical_mappings[section_code][chapter_code][heading_code]
        heading_path["sub_headings"][sub_heading_code] = sub_heading_name
    
    def get_sections(self) -> Dict[str, str]:
        """Get all sections"""
        return self._section_map.copy()
    
    def get_chapters(self, section_code: str) -> Dict[str, str]:
        """Get chapters for a section"""
        return self._hierarchical_mappings.get(section_code, {}).get("chapters", {})
    
    def get_headings(self, section_code: str, chapter_code: str) -> Dict[str, str]:
        """Get headings for a chapter"""
        section_data = self._hierarchical_mappings.get(section_code, {})
        return section_data.get(chapter_code, {}).get("headings", {})
    
    def get_sub_headings(self, section_code: str, chapter_code: str, heading_code: str) -> Dict[str, str]:
        """Get sub-headings for a heading"""
        section_data = self._hierarchical_mappings.get(section_code, {})
        chapter_data = section_data.get(chapter_code, {})
        return chapter_data.get(heading_code, {}).get("sub_headings", {})
    
    def get_available_labels(self, level: ClassificationLevel, parent_path: List[str]) -> Dict[str, str]:
        """Get available labels for a given level based on parent path"""
        if level == ClassificationLevel.SECTIONS:
            return self._section_map
        
        if not parent_path:
            return {}
        
        try:
            if level == ClassificationLevel.CHAPTERS:
                return self.get_chapters(parent_path[0])
            elif level == ClassificationLevel.HEADINGS:
                return self.get_headings(parent_path[0], parent_path[1])
            elif level == ClassificationLevel.SUB_HEADINGS:
                return self.get_sub_headings(parent_path[0], parent_path[1], parent_path[2])
        except (IndexError, KeyError):
            return {}
        
        return {}

class LevelClassifier:
    """
    Handles classification for a specific level with specific labels.
    Each unique combination of level and parent path gets its own classifier.
    """
    
    def __init__(self, classifier_id: str, label_mapping: Dict[str, str]):
        self.classifier_id = classifier_id
        self.embeddings: Optional[Dict[str, np.ndarray]] = None
        self.label_mapping = label_mapping
        self.label_names = list(label_mapping.keys())
        
        # Create classifier-specific directories
        self.cache_dir = os.path.join(EMBEDDINGS_BASE_DIR, classifier_id)
        self.embeddings_file = os.path.join(self.cache_dir, "embeddings.pkl")
        self.hash_file = os.path.join(self.cache_dir, "labels_hash.txt")
        
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _get_labels_hash(self) -> str:
        """Generate a hash of the label names to detect changes"""
        labels_str = json.dumps(sorted(self.label_names))
        return hashlib.md5(labels_str.encode()).hexdigest()
    
    def _save_embeddings_to_file(self):
        """Save embeddings and labels hash to files"""
        try:
            with open(self.embeddings_file, 'wb') as f:
                pickle.dump(self.embeddings, f)
            
            with open(self.hash_file, 'w') as f:
                f.write(self._get_labels_hash())
            
            print(f"  ✓ {self.classifier_id} embeddings saved")
        except Exception as e:
            print(f"  ✗ Warning: Failed to save {self.classifier_id} embeddings: {e}")
    
    def _load_embeddings_from_file(self) -> bool:
        """Load embeddings from file if they exist and are valid"""
        try:
            if not (os.path.exists(self.embeddings_file) and os.path.exists(self.hash_file)):
                return False
            
            with open(self.hash_file, 'r') as f:
                stored_hash = f.read().strip()
            
            current_hash = self._get_labels_hash()
            if stored_hash != current_hash:
                print(f"  → Labels changed for {self.classifier_id}, regenerating...")
                return False
            
            with open(self.embeddings_file, 'rb') as f:
                self.embeddings = pickle.load(f)
            
            if not isinstance(self.embeddings, dict) or set(self.embeddings.keys()) != set(self.label_names):
                return False
            
            print(f"  ✓ Loaded cached embeddings for {self.classifier_id}")
            return True
            
        except Exception as e:
            print(f"  ✗ Error loading {self.classifier_id} embeddings: {e}")
            return False
    
    async def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding from Ollama API"""
        url = f"{OLLAMA_BASE_URL}/api/embeddings"
        payload = {"model": MODEL_NAME, "prompt": text}
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        raise Exception(f"Ollama API error: {response.status}")
                    
                    data = await response.json()
                    return np.array(data["embedding"])
                    
            except aiohttp.ClientError as e:
                raise Exception(f"Failed to connect to Ollama: {str(e)}")
    
    async def initialize_embeddings(self):
        """Load embeddings from file or generate new ones if needed"""
        if self.embeddings is not None:
            return
        
        if not self.label_names:
            print(f"  ⚠ No labels defined for {self.classifier_id}")
            return
        
        # Try to load from file first
        if self._load_embeddings_from_file():
            return
        
        # Generate new embeddings
        print(f"  → Generating embeddings for {self.classifier_id}...")
        self.embeddings = {}
        
        for i, label_name in enumerate(self.label_names, 1):
            print(f"    Processing {i}/{len(self.label_names)}: {label_name}")
            
            # Create descriptive text for embedding
            descriptive_text = f"{label_name} classification category"
            embedding = await self.get_embedding(descriptive_text)
            self.embeddings[label_name] = embedding
        
        # Save embeddings to file
        self._save_embeddings_to_file()
        print(f"  ✓ {self.classifier_id} embeddings initialized!")
    
    async def classify(self, text: str) -> ClassificationResult:
        """Classify input text into one of the labels"""
        await self.initialize_embeddings()
        
        if not self.embeddings:
            raise Exception(f"No embeddings available for classifier {self.classifier_id}")
        
        # Get embedding for input text
        input_embedding = await self.get_embedding(text)
        
        # Calculate cosine similarities
        similarities = {}
        for label_name, label_embedding in self.embeddings.items():
            input_emb_2d = input_embedding.reshape(1, -1)
            label_emb_2d = label_embedding.reshape(1, -1)
            
            similarity = cosine_similarity(input_emb_2d, label_emb_2d)[0][0]
            similarities[label_name] = float(similarity)
        
        # Find the label with highest similarity
        best_label = max(similarities, key=similarities.get)
        best_score = similarities[best_label]
        
        return ClassificationResult(
            predicted_label=best_label,
            label_code=self.label_mapping[best_label],
            confidence_score=best_score,
            all_scores=similarities,
            level=ClassificationLevel.SECTIONS  # Will be overridden by caller
        )

class HierarchicalClassifier:
    """
    Main classifier that handles the complete hierarchical classification system.
    Supports dynamic expansion and multiple classification strategies.
    """
    
    def __init__(self, mappings_file: Optional[str] = None):
        self.mapping_loader = HierarchicalMappingLoader(mappings_file)
        self.level_classifiers: Dict[str, LevelClassifier] = {}
        
        # Initialize base sections classifier
        sections_mapping = self.mapping_loader.get_sections()
        self.level_classifiers['sections'] = LevelClassifier('sections', sections_mapping)
    
    def _get_classifier_key(self, level: ClassificationLevel, parent_path: List[str]) -> str:
        """Generate a unique key for the classifier based on level and parent path"""
        if level == ClassificationLevel.SECTIONS:
            return "sections"
        
        path_str = "_".join(parent_path) if parent_path else ""
        return f"{level.value}_{path_str}"
    
    async def _get_or_create_classifier(self, level: ClassificationLevel, parent_path: List[str]) -> LevelClassifier:
        """Get or create a classifier for the specific level and parent path"""
        classifier_key = self._get_classifier_key(level, parent_path)
        
        if classifier_key not in self.level_classifiers:
            label_mapping = self.mapping_loader.get_available_labels(level, parent_path)
            if not label_mapping:
                raise Exception(f"No labels available for {level.value} with parent path {parent_path}")
            
            self.level_classifiers[classifier_key] = LevelClassifier(classifier_key, label_mapping)
        
        return self.level_classifiers[classifier_key]
    
    async def initialize_base_embeddings(self):
        """Initialize embeddings for the base sections classifier"""
        print("Initializing base sections classifier...")
        await self.level_classifiers['sections'].initialize_embeddings()
        print("Base sections classifier initialized!")
    
    async def classify_single_level(
        self, 
        text: str, 
        level: ClassificationLevel,
        parent_path: Optional[List[str]] = None
    ) -> ClassificationResult:
        """Classify text at a single level given the parent path"""
        parent_path = parent_path or []
        classifier = await self._get_or_create_classifier(level, parent_path)
        
        result = await classifier.classify(text)
        result.level = level
        return result
    
    async def classify_hierarchical(
        self, 
        text: str, 
        max_depth: Optional[int] = None,
        stop_on_low_confidence: Optional[float] = None
    ) -> HierarchicalResult:
        """
        Classify text through hierarchical levels.
        
        Args:
            text: Text to classify
            max_depth: Maximum depth to classify (1=sections only, 4=all levels)
            stop_on_low_confidence: Stop if confidence drops below this threshold
        """
        import time
        start_time = time.time()
        
        classification_path = []
        parent_path = []
        full_code_parts = []
        
        levels = [
            ClassificationLevel.SECTIONS,
            ClassificationLevel.CHAPTERS,
            ClassificationLevel.HEADINGS,
            ClassificationLevel.SUB_HEADINGS
        ]
        
        current_depth = 0
        max_depth = max_depth or len(levels)
        
        for level in levels:
            if current_depth >= max_depth:
                break
                
            try:
                # Classify at current level
                result = await self.classify_single_level(text, level, parent_path)
                
                # Check confidence threshold
                if stop_on_low_confidence and result.confidence_score < stop_on_low_confidence:
                    print(f"Stopping at {level.value} due to low confidence: {result.confidence_score:.4f}")
                    break
                
                classification_path.append(result)
                
                # Update parent path with the predicted code
                parent_path.append(result.label_code)
                full_code_parts.append(result.label_code)
                
                current_depth += 1
                
                # Check if next level has available labels
                if current_depth < len(levels):
                    next_level = levels[current_depth]
                    available_labels = self.mapping_loader.get_available_labels(next_level, parent_path)
                    if not available_labels:
                        print(f"No labels available for {next_level.value} with path {parent_path}")
                        break
                        
            except Exception as e:
                print(f"Stopping classification at {level.value}: {e}")
                break
        
        processing_time = (time.time() - start_time) * 1000
        full_code = ".".join(full_code_parts)
        
        return HierarchicalResult(
            text=text,
            classification_path=classification_path,
            full_code=full_code,
            processing_time_ms=round(processing_time, 2)
        )
    
    def add_section(self, section_name: str, section_code: str):
        """Add a new section and reinitialize if needed"""
        self.mapping_loader.add_section(section_name, section_code)
        # Reset sections classifier to include new section
        if 'sections' in self.level_classifiers:
            self.level_classifiers['sections'].embeddings = None
    
    def add_chapter(self, section_code: str, chapter_name: str, chapter_code: str):
        """Add a new chapter to a section"""
        self.mapping_loader.add_chapter(section_code, chapter_name, chapter_code)
        # Reset relevant classifiers
        chapters_key = f"chapters_{section_code}"
        if chapters_key in self.level_classifiers:
            self.level_classifiers[chapters_key].embeddings = None
    
    def add_heading(self, section_code: str, chapter_code: str, heading_name: str, heading_code: str):
        """Add a new heading to a chapter"""
        self.mapping_loader.add_heading(section_code, chapter_code, heading_name, heading_code)
        # Reset relevant classifiers
        headings_key = f"headings_{section_code}_{chapter_code}"
        if headings_key in self.level_classifiers:
            self.level_classifiers[headings_key].embeddings = None
    
    def add_sub_heading(self, section_code: str, chapter_code: str, heading_code: str, 
                       sub_heading_code: str, sub_heading_name: str):
        """Add a new sub-heading to a heading"""
        self.mapping_loader.add_sub_heading(section_code, chapter_code, heading_code, 
                                          sub_heading_code, sub_heading_name)
        # Reset relevant classifiers
        sub_headings_key = f"sub_headings_{section_code}_{chapter_code}_{heading_code}"
        if sub_headings_key in self.level_classifiers:
            self.level_classifiers[sub_headings_key].embeddings = None
    
    def save_mappings(self, filepath: str):
        """Save current mappings to file"""
        self.mapping_loader.save_mappings_to_file(filepath)
    
    def get_classification_structure(self) -> Dict:
        """Get the complete classification structure"""
        return {
            "sections": self.mapping_loader.get_sections(),
            "total_sections": len(self.mapping_loader.get_sections()),
            "initialized_classifiers": list(self.level_classifiers.keys())
        }
    
    def clear_all_caches(self):
        """Clear all embedding caches"""
        for classifier in self.level_classifiers.values():
            classifier.embeddings = None
            # Remove cache files
            if os.path.exists(classifier.embeddings_file):
                os.remove(classifier.embeddings_file)
            if os.path.exists(classifier.hash_file):
                os.remove(classifier.hash_file)
    
    def get_cache_status(self) -> Dict:
        """Get status of all caches"""
        status = {}
        for classifier_id, classifier in self.level_classifiers.items():
            embeddings_exist = os.path.exists(classifier.embeddings_file)
            status[classifier_id] = {
                "embeddings_loaded": classifier.embeddings is not None,
                "cache_file_exists": embeddings_exist,
                "labels_count": len(classifier.label_names),
                "labels": classifier.label_names
            }
        return status

# Example usage and testing functions
async def example_usage():
    """Example of how to use the hierarchical classifier"""
    
    # Initialize classifier
    classifier = HierarchicalClassifier()
    await classifier.initialize_base_embeddings()
    
    # Example: Add new sections, chapters, headings, sub-headings
    classifier.add_section("New Category", "XXII")
    classifier.add_chapter("I", "New Animal Type", "6")
    classifier.add_heading("I", "1", "New Livestock", "7")
    classifier.add_sub_heading("I", "1", "1", "0101.99.00", "Special Horses")
    
    # Save updated structure
    classifier.save_mappings("updated_mappings.json")
    
    # Test classifications
    test_inputs = [
        "breeding horses",
        "live cattle",
        "cotton fabric",
        "leather shoes"
    ]
    
    print("=== Hierarchical Classification Examples ===\n")
    
    for text in test_inputs:
        try:
            print(f"Input: '{text}'")
            
            # Hierarchical classification
            result = await classifier.classify_hierarchical(
                text, 
                max_depth=4,
                stop_on_low_confidence=0.3
            )
            
            print(f"Full Code: {result.full_code}")
            print("Classification Path:")
            for classification in result.classification_path:
                print(f"  {classification.level.value}: "
                      f"{classification.predicted_label} ({classification.label_code}) "
                      f"- {classification.confidence_score:.4f}")
            
            print(f"Processing time: {result.processing_time_ms}ms\n")
            
        except Exception as e:
            print(f"Error: {e}\n")

# Helper function to create mappings file
def create_mappings_file(filepath: str):
    """Create a template mappings file for easy extension"""
    template = {
        "sections": {
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
            "Art/Antiques": "XXI"
        },
        "hierarchical_mappings": {
            "I": {
                "chapters": {
                    "Livestock": "1",
                    "Meat": "2",
                    "Seafood": "3",
                    "Dairy": "4",
                    "Byproducts": "5"
                },
                "1": {
                    "headings": {
                        "Horses": "1",
                        "Cattle": "2",
                        "Swine": "3",
                        "Sheep/Goats": "4",
                        "Poultry": "5",
                        "Other": "6"
                    },
                    "1": {
                        "sub_headings": {
                            "0101.21.00": "Breeding",
                            "0101.29.00": "Other",
                            "0101.30.00": "Asses",
                            "0101.90.00": "Other"
                        }
                    }
                }
            }
        }
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=2, ensure_ascii=False)
    print(f"Template mappings file created: {filepath}")

if __name__ == "__main__":
    # Create template file
    create_mappings_file("classification_mappings.json")
    
    # Run example
    asyncio.run(example_usage())SECTIONS = "sections"
    CHAPTERS = "chapters"
    HEADINGS = "headings"
    SUB_HEADINGS = "sub_headings"

@dataclass
class ClassificationResult:
    predicted_label: str
    label_code: str
    confidence_score: float
    all_scores: Dict[str, float]
    level: ClassificationLevel

@dataclass
class HierarchicalResult:
    text: str
    classification_path: List[ClassificationResult]
    full_code: str
    processing_time_ms: float

class HierarchicalMappingLoader:
    """
    Handles loading and managing hierarchical mappings.
    Supports both static definition and dynamic loading from files.
    """
    
    def __init__(self, mappings_file: Optional[str] = None):
        self.mappings_file = mappings_file
        self._section_map = {}
        self._hierarchical_mappings = {}
        self._load_mappings()
    
    def _load_mappings(self):
        """Load mappings from file or use default structure"""
        if self.mappings_file and os.path.exists(self.mappings_file):
            self._load_from_file()
        else:
            self._load_default_mappings()
    
    def _load_from_file(self):
        """Load mappings from JSON file"""
        try:
            with open(self.mappings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._section_map = data.get('sections', {})
                self._hierarchical_mappings = data.get('hierarchical_mappings', {})
            print(f"Loaded mappings from {self.mappings_file}")
        except Exception as e:
            print(f"Error loading mappings from file: {e}")
            self._load_default_mappings()
    
    def _load_default_mappings(self):
        """Load default mappings structure"""
        self._section_map = {
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
        
        # Example hierarchical mappings - extend this structure
        self._hierarchical_mappings = {
            "I": {  # Animals section
                "chapters": {
                    "Livestock": "1",
                    "Meat": "2",
                    "Seafood": "3",
                    "Dairy": "4",
                    "Byproducts": "5",
                },
                "1": {  # Livestock chapter
                    "headings": {
                        "Horses": "1",
                        "Cattle": "2",
                        "Swine": "3",
                        "Sheep/Goats": "4",
                        "Poultry": "5",
                        "Other": "6",
                    },
                    "1": {  # Horses heading
                        "sub_headings": {
                            "0101.21.00": "Breeding",
                            "0101.29.00": "Other",
                            "0101.30.00": "Asses",
                            "0101.90.00": "Other",
                        }
                    },
                    "2": {  # Cattle heading
                        "sub_headings": {
                            "0102.21.00": "Breeding Cattle",
                            "0102.29.00": "Other Cattle",
                            "0102.31.00": "Buffalo",
                            "0102.90.00": "Other Bovine",
                        }
                    },
                },
                "2": {  # Meat chapter
                    "headings": {
                        "Beef": "1",
                        "Pork": "2",
                        "Lamb": "3",
                        "Poultry": "4",
                        "Other": "5",
                    },
                },
            },
            # Add more sections here as needed
        }