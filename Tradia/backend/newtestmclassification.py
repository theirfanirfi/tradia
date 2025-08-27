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

# Confidence thresholds for different levels
DEFAULT_CONFIDENCE_THRESHOLDS = {
    "sections": 0.45,      # Higher threshold for initial classification
    "chapters": 0.40,      # Slightly lower for chapters
    "headings": 0.35,      # Lower for more specific items
    "subheadings": 0.30    # Lowest for final classification
}

class ClassificationLevel(str, Enum):
    SECTIONS = "sections"
    CHAPTERS = "chapters"
    HEADINGS = "headings"
    SUBHEADINGS = "subheadings"

@dataclass
class TariffEntry:
    """Represents a single tariff classification entry"""
    section: str
    chapter_number: str
    chapter_title: str
    chapter_url: str
    table_caption: str
    reference_number: str
    subheading: str
    indent_level: int
    statistical_code: str
    unit: str
    rate: str
    tco_text: str
    tco_href: str

@dataclass
class ClassificationResult:
    predicted_label: str
    label_code: str
    confidence_score: float
    all_scores: Dict[str, float]
    level: ClassificationLevel
    meets_threshold: bool = True
    metadata: Optional[Dict] = None

@dataclass
class HierarchicalResult:
    text: str
    classification_path: List[ClassificationResult]
    full_code: str
    processing_time_ms: float
    final_tariff_entry: Optional[TariffEntry] = None
    classification_stopped: bool = False
    stop_reason: Optional[str] = None

class TariffDataProcessor:
    """
    Processes tariff data from the structured format and builds hierarchical mappings.
    """
    
    def __init__(self):
        self.tariff_entries: List[TariffEntry] = []
        self.section_mappings: Dict[str, Dict] = {}
    
    def load_from_json_lines(self, filepath: str):
        """Load tariff data from JSON lines file"""
        self.tariff_entries = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        data = json.loads(line)
                        entry = TariffEntry(**data)
                        self.tariff_entries.append(entry)
                    except json.JSONDecodeError as e:
                        print(f"Error parsing line {line_num}: {e}")
                    except TypeError as e:
                        print(f"Error creating TariffEntry from line {line_num}: {e}")
            
            print(f"Loaded {len(self.tariff_entries)} tariff entries from {filepath}")
            self._build_hierarchical_mappings()
            
        except FileNotFoundError:
            print(f"File not found: {filepath}")
        except Exception as e:
            print(f"Error loading tariff data: {e}")
    
    def add_tariff_entry(self, entry_data: Dict):
        """Add a single tariff entry"""
        try:
            entry = TariffEntry(**entry_data)
            self.tariff_entries.append(entry)
            self._build_hierarchical_mappings()
        except Exception as e:
            print(f"Error adding tariff entry: {e}")
    
    def _build_hierarchical_mappings(self):
        """Build hierarchical mappings from tariff entries"""
        self.section_mappings = {}
        
        # Group entries by section
        sections = {}
        for entry in self.tariff_entries:
            section_key = entry.section.upper()
            if section_key not in sections:
                sections[section_key] = {
                    'chapters': {},
                    'entries': []
                }
            sections[section_key]['entries'].append(entry)
        
        # Process each section
        for section_key, section_data in sections.items():
            chapters = {}
            
            # Group by chapter
            for entry in section_data['entries']:
                chapter_key = entry.chapter_number
                if chapter_key not in chapters:
                    chapters[chapter_key] = {
                        'title': entry.chapter_title,
                        'url': entry.chapter_url,
                        'headings': {},
                        'entries': []
                    }
                chapters[chapter_key]['entries'].append(entry)
            
            # Process each chapter
            for chapter_key, chapter_data in chapters.items():
                headings = {}
                
                # Group by reference number (heading level)
                for entry in chapter_data['entries']:
                    # Extract heading from reference number
                    ref_parts = entry.reference_number.split('.')
                    if len(ref_parts) >= 1:
                        heading_key = ref_parts[0]  # e.g., "0101"
                        
                        if heading_key not in headings:
                            headings[heading_key] = {
                                'caption': entry.table_caption,
                                'subheadings': {},
                                'entries': []
                            }
                        headings[heading_key]['entries'].append(entry)
                
                chapter_data['headings'] = headings
            
            self.section_mappings[section_key] = {
                'name': f"Section {section_key.upper()}",
                'chapters': chapters
            }
        
        print(f"Built hierarchical mappings for {len(self.section_mappings)} sections")
    
    def get_sections(self) -> Dict[str, str]:
        """Get all sections with their names"""
        return {
            data['name']: section_key 
            for section_key, data in self.section_mappings.items()
        }
    
    def get_chapters(self, section_code: str) -> Dict[str, str]:
        """Get chapters for a section"""
        section_data = self.section_mappings.get(section_code.upper(), {})
        chapters = section_data.get('chapters', {})
        return {
            f"{chapter_key}: {chapter_data['title']}": chapter_key
            for chapter_key, chapter_data in chapters.items()
        }
    
    def get_headings(self, section_code: str, chapter_code: str) -> Dict[str, str]:
        """Get headings (reference numbers) for a chapter"""
        section_data = self.section_mappings.get(section_code.upper(), {})
        chapters = section_data.get('chapters', {})
        chapter_data = chapters.get(chapter_code, {})
        headings = chapter_data.get('headings', {})
        
        return {
            f"{heading_key}: {heading_data['caption']}": heading_key
            for heading_key, heading_data in headings.items()
        }
    
    def get_subheadings(self, section_code: str, chapter_code: str, heading_code: str) -> Dict[str, str]:
        """Get subheadings for a heading"""
        section_data = self.section_mappings.get(section_code.upper(), {})
        chapters = section_data.get('chapters', {})
        chapter_data = chapters.get(chapter_code, {})
        headings = chapter_data.get('headings', {})
        heading_data = headings.get(heading_code, {})
        
        # Get entries for this heading and extract subheadings
        entries = heading_data.get('entries', [])
        subheadings = {}
        
        for entry in entries:
            # Only include entries with full reference numbers (subheadings)
            if '.' in entry.reference_number and entry.statistical_code:
                clean_subheading = entry.subheading.strip('- ').strip()
                subheadings[f"{entry.reference_number}: {clean_subheading}"] = entry.reference_number
        
        return subheadings
    
    def get_tariff_entry(self, reference_number: str) -> Optional[TariffEntry]:
        """Get the full tariff entry for a reference number"""
        for entry in self.tariff_entries:
            if entry.reference_number == reference_number:
                return entry
        return None
    
    def get_available_labels(self, level: ClassificationLevel, parent_path: List[str]) -> Dict[str, str]:
        """Get available labels for a given level based on parent path"""
        if level == ClassificationLevel.SECTIONS:
            return self.get_sections()
        elif level == ClassificationLevel.CHAPTERS and len(parent_path) >= 1:
            return self.get_chapters(parent_path[0])
        elif level == ClassificationLevel.HEADINGS and len(parent_path) >= 2:
            return self.get_headings(parent_path[0], parent_path[1])
        elif level == ClassificationLevel.SUBHEADINGS and len(parent_path) >= 3:
            return self.get_subheadings(parent_path[0], parent_path[1], parent_path[2])
        
        return {}

class LevelClassifier:
    """
    Handles classification for a specific level with specific labels.
    """
    
    def __init__(self, classifier_id: str, label_mapping: Dict[str, str], confidence_threshold: float = 0.3):
        self.classifier_id = classifier_id
        self.embeddings: Optional[Dict[str, np.ndarray]] = None
        self.label_mapping = label_mapping
        self.label_names = list(label_mapping.keys())
        self.confidence_threshold = confidence_threshold
        
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
            print(f"    Processing {i}/{len(self.label_names)}: {label_name[:50]}...")
            
            # Create descriptive text for embedding
            embedding = await self.get_embedding(label_name)
            self.embeddings[label_name] = embedding
        
        # Save embeddings to file
        self._save_embeddings_to_file()
        print(f"  ✓ {self.classifier_id} embeddings initialized!")
    
    def _calculate_semantic_similarity(self, input_embedding: np.ndarray, label_embedding: np.ndarray) -> float:
        """Calculate semantic similarity with additional validation"""
        # Basic cosine similarity
        input_emb_2d = input_embedding.reshape(1, -1)
        label_emb_2d = label_embedding.reshape(1, -1)
        
        cosine_sim = cosine_similarity(input_emb_2d, label_emb_2d)[0][0]
        
        # Additional validation: check embedding magnitude similarity
        input_norm = np.linalg.norm(input_embedding)
        label_norm = np.linalg.norm(label_embedding)
        norm_ratio = min(input_norm, label_norm) / max(input_norm, label_norm)
        
        # Penalize if embeddings have very different magnitudes (could indicate different domains)
        if norm_ratio < 0.7:
            cosine_sim *= 0.8  # Reduce similarity score
        
        return float(cosine_sim)
    
    async def classify(self, text: str) -> ClassificationResult:
        """Classify input text into one of the labels with confidence validation"""
        await self.initialize_embeddings()
        
        if not self.embeddings:
            raise Exception(f"No embeddings available for classifier {self.classifier_id}")
        
        # Get embedding for input text
        input_embedding = await self.get_embedding(text)
        
        # Calculate similarities with enhanced validation
        similarities = {}
        for label_name, label_embedding in self.embeddings.items():
            similarity = self._calculate_semantic_similarity(input_embedding, label_embedding)
            similarities[label_name] = similarity
        
        # Find the label with highest similarity
        best_label = max(similarities, key=similarities.get)
        best_score = similarities[best_label]
        
        # Check if the best score meets the confidence threshold
        meets_threshold = best_score >= self.confidence_threshold
        
        # Additional validation: check if second-best score is very close (ambiguous classification)
        sorted_scores = sorted(similarities.values(), reverse=True)
        if len(sorted_scores) > 1:
            score_gap = sorted_scores[0] - sorted_scores[1]
            if score_gap < 0.05:  # Very close scores indicate ambiguous classification
                meets_threshold = False
        
        return ClassificationResult(
            predicted_label=best_label,
            label_code=self.label_mapping[best_label],
            confidence_score=best_score,
            all_scores=similarities,
            level=ClassificationLevel.SECTIONS,  # Will be overridden by caller
            meets_threshold=meets_threshold
        )

class TariffClassifier:
    """
    Main tariff classification system that handles hierarchical classification
    using real tariff data structure with improved confidence validation.
    """
    
    def __init__(self, tariff_data_file: Optional[str] = None, confidence_thresholds: Optional[Dict[str, float]] = None):
        self.tariff_processor = TariffDataProcessor()
        self.level_classifiers: Dict[str, LevelClassifier] = {}
        self.confidence_thresholds = confidence_thresholds or DEFAULT_CONFIDENCE_THRESHOLDS.copy()
        
        # Load tariff data if provided
        if tariff_data_file and os.path.exists(tariff_data_file):
            self.tariff_processor.load_from_json_lines(tariff_data_file)
            self._initialize_base_classifier()
    
    def load_tariff_data(self, filepath: str):
        """Load tariff data from file"""
        self.tariff_processor.load_from_json_lines(filepath)
        self._initialize_base_classifier()
    
    def add_tariff_entries(self, entries: List[Dict]):
        """Add multiple tariff entries"""
        for entry in entries:
            self.tariff_processor.add_tariff_entry(entry)
        self._initialize_base_classifier()
    
    def set_confidence_thresholds(self, thresholds: Dict[str, float]):
        """Update confidence thresholds for different levels"""
        self.confidence_thresholds.update(thresholds)
        # Update existing classifiers
        for classifier_id, classifier in self.level_classifiers.items():
            level = classifier_id.split('_')[0]
            if level in self.confidence_thresholds:
                classifier.confidence_threshold = self.confidence_thresholds[level]
    
    def _initialize_base_classifier(self):
        """Initialize the base sections classifier"""
        sections_mapping = self.tariff_processor.get_sections()
        if sections_mapping:
            threshold = self.confidence_thresholds.get('sections', 0.45)
            self.level_classifiers['sections'] = LevelClassifier('sections', sections_mapping, threshold)
    
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
            label_mapping = self.tariff_processor.get_available_labels(level, parent_path)
            if not label_mapping:
                raise Exception(f"No labels available for {level.value} with parent path {parent_path}")
            
            threshold = self.confidence_thresholds.get(level.value, 0.3)
            self.level_classifiers[classifier_key] = LevelClassifier(classifier_key, label_mapping, threshold)
        
        return self.level_classifiers[classifier_key]
    
    async def initialize_base_embeddings(self):
        """Initialize embeddings for the base sections classifier"""
        if 'sections' in self.level_classifiers:
            print("Initializing base sections classifier...")
            await self.level_classifiers['sections'].initialize_embeddings()
            print("Base sections classifier initialized!")
        else:
            print("No tariff data loaded. Please load tariff data first.")
    
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
        include_tariff_details: bool = True,
        strict_mode: bool = True
    ) -> HierarchicalResult:
        """
        Classify text through hierarchical levels with improved confidence validation.
        
        Args:
            text: Input text to classify
            max_depth: Maximum depth to classify (None for full depth)
            include_tariff_details: Whether to include final tariff entry details
            strict_mode: If True, stops immediately on confidence failure
        """
        import time
        start_time = time.time()
        
        classification_path = []
        parent_path = []
        full_code_parts = []
        final_tariff_entry = None
        classification_stopped = False
        stop_reason = None
        
        levels = [
            ClassificationLevel.SECTIONS,
            ClassificationLevel.CHAPTERS,
            ClassificationLevel.HEADINGS,
            ClassificationLevel.SUBHEADINGS
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
                if not result.meets_threshold:
                    classification_stopped = True
                    stop_reason = f"Low confidence at {level.value}: {result.confidence_score:.4f} < {self.confidence_thresholds.get(level.value, 0.3):.4f}"
                    
                    # In strict mode, stop immediately
                    if strict_mode:
                        print(f"STOPPING: {stop_reason}")
                        break
                    else:
                        # In non-strict mode, include the result but mark it as unreliable
                        print(f"WARNING: {stop_reason} (continuing in non-strict mode)")
                
                classification_path.append(result)
                
                # Update parent path with the predicted code
                parent_path.append(result.label_code)
                full_code_parts.append(result.label_code)
                
                # If this is the final subheading level and we want tariff details
                if level == ClassificationLevel.SUBHEADINGS and include_tariff_details:
                    final_tariff_entry = self.tariff_processor.get_tariff_entry(result.label_code)
                
                current_depth += 1
                
                # Check if next level has available labels
                if current_depth < len(levels):
                    next_level = levels[current_depth]
                    available_labels = self.tariff_processor.get_available_labels(next_level, parent_path)
                    if not available_labels:
                        classification_stopped = True
                        stop_reason = f"No labels available for {next_level.value} with path {parent_path}"
                        print(f"STOPPING: {stop_reason}")
                        break
                        
            except Exception as e:
                classification_stopped = True
                stop_reason = f"Error at {level.value}: {str(e)}"
                print(f"STOPPING: {stop_reason}")
                break
        
        processing_time = (time.time() - start_time) * 1000
        full_code = ".".join(full_code_parts)
        
        return HierarchicalResult(
            text=text,
            classification_path=classification_path,
            full_code=full_code,
            processing_time_ms=round(processing_time, 2),
            final_tariff_entry=final_tariff_entry,
            classification_stopped=classification_stopped,
            stop_reason=stop_reason
        )
    
    def get_tariff_structure_summary(self) -> Dict:
        """Get summary of the loaded tariff structure"""
        sections = self.tariff_processor.get_sections()
        total_chapters = 0
        total_headings = 0
        total_subheadings = 0
        
        for section_code in sections.values():
            chapters = self.tariff_processor.get_chapters(section_code)
            total_chapters += len(chapters)
            
            for chapter_code in chapters.values():
                headings = self.tariff_processor.get_headings(section_code, chapter_code)
                total_headings += len(headings)
                
                for heading_code in headings.values():
                    subheadings = self.tariff_processor.get_subheadings(section_code, chapter_code, heading_code)
                    total_subheadings += len(subheadings)
        
        return {
            "total_sections": len(sections),
            "total_chapters": total_chapters,
            "total_headings": total_headings,
            "total_subheadings": total_subheadings,
            "total_entries": len(self.tariff_processor.tariff_entries),
            "initialized_classifiers": list(self.level_classifiers.keys()),
            "confidence_thresholds": self.confidence_thresholds
        }
    
    def search_tariff_entries(self, search_term: str, max_results: int = 10) -> List[TariffEntry]:
        """Search tariff entries by text content"""
        results = []
        search_lower = search_term.lower()
        
        for entry in self.tariff_processor.tariff_entries:
            if (search_lower in entry.subheading.lower() or 
                search_lower in entry.table_caption.lower() or
                search_lower in entry.chapter_title.lower()):
                results.append(entry)
                
                if len(results) >= max_results:
                    break
        
        return results
    
    def get_cache_status(self) -> Dict:
        """Get status of all caches"""
        status = {}
        for classifier_id, classifier in self.level_classifiers.items():
            embeddings_exist = os.path.exists(classifier.embeddings_file)
            status[classifier_id] = {
                "embeddings_loaded": classifier.embeddings is not None,
                "cache_file_exists": embeddings_exist,
                "labels_count": len(classifier.label_names),
                "confidence_threshold": classifier.confidence_threshold
            }
            
            if embeddings_exist:
                file_stats = os.stat(classifier.embeddings_file)
                status[classifier_id]["cache_file_size_mb"] = round(file_stats.st_size / (1024*1024), 2)
                status[classifier_id]["cache_file_modified"] = file_stats.st_mtime
        
        return status
    
    def clear_all_caches(self):
        """Clear all embedding caches"""
        for classifier in self.level_classifiers.values():
            classifier.embeddings = None
            # Remove cache files
            if os.path.exists(classifier.embeddings_file):
                os.remove(classifier.embeddings_file)
            if os.path.exists(classifier.hash_file):
                os.remove(classifier.hash_file)



import asyncio
import json
from typing import Dict, List

# Import the existing classes (assuming they're in the same file or imported)
# from your_tariff_module import TariffClassifier, TariffEntry, ClassificationLevel

# Section mapping provided
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

def create_comprehensive_test_data() -> List[Dict]:
    """Create comprehensive test data covering multiple sections"""
    
    test_data = [
        # Section I - Animals
        {
            "section": "I", "chapter_number": "01", "chapter_title": "Live animals",
            "chapter_url": "https://www.abf.gov.au/importing-exporting-and-manufacturing/tariff-classification/current-tariff/schedule-3/section-i/chapter-1",
            "table_caption": "Live horses, asses, mules and hinnies", "reference_number": "0101",
            "subheading": "LIVE HORSES, ASSES, MULES AND HINNIES:", "indent_level": 0,
            "statistical_code": "", "unit": "", "rate": "", "tco_text": "", "tco_href": ""
        },
        {
            "section": "I", "chapter_number": "01", "chapter_title": "Live animals",
            "chapter_url": "https://www.abf.gov.au/importing-exporting-and-manufacturing/tariff-classification/current-tariff/schedule-3/section-i/chapter-1",
            "table_caption": "Live horses, asses, mules and hinnies", "reference_number": "0101.21.00",
            "subheading": "-- Pure-bred breeding animals", "indent_level": 1,
            "statistical_code": "21", "unit": "No", "rate": "Free", "tco_text": "View TCOs for 0101.21.00", "tco_href": "https://www.abf.gov.au"
        },
        {
            "section": "I", "chapter_number": "01", "chapter_title": "Live animals",
            "chapter_url": "https://www.abf.gov.au/importing-exporting-and-manufacturing/tariff-classification/current-tariff/schedule-3/section-i/chapter-1",
            "table_caption": "Live horses, asses, mules and hinnies", "reference_number": "0101.29.00",
            "subheading": "-- Other horses", "indent_level": 1,
            "statistical_code": "29", "unit": "No", "rate": "Free", "tco_text": "View TCOs for 0101.29.00", "tco_href": "https://www.abf.gov.au"
        },
        {
            "section": "I", "chapter_number": "02", "chapter_title": "Meat and edible meat offal",
            "chapter_url": "https://example.com", "table_caption": "Bovine meat, fresh or chilled",
            "reference_number": "0201", "subheading": "MEAT OF BOVINE ANIMALS, FRESH OR CHILLED:",
            "indent_level": 0, "statistical_code": "", "unit": "", "rate": "", "tco_text": "", "tco_href": ""
        },
        {
            "section": "I", "chapter_number": "02", "chapter_title": "Meat and edible meat offal",
            "chapter_url": "https://example.com", "table_caption": "Bovine meat, fresh or chilled",
            "reference_number": "0201.10.00", "subheading": "- Carcasses and half-carcasses",
            "indent_level": 1, "statistical_code": "10", "unit": "kg", "rate": "Free", "tco_text": "", "tco_href": ""
        },
        
        # Section IV - Food/Drink
        {
            "section": "IV", "chapter_number": "20", "chapter_title": "Preparations of vegetables, fruit, nuts",
            "chapter_url": "https://example.com", "table_caption": "Tomato preparations",
            "reference_number": "2002", "subheading": "TOMATOES PREPARED OR PRESERVED OTHERWISE THAN BY VINEGAR OR ACETIC ACID:",
            "indent_level": 0, "statistical_code": "", "unit": "", "rate": "", "tco_text": "", "tco_href": ""
        },
        {
            "section": "IV", "chapter_number": "20", "chapter_title": "Preparations of vegetables, fruit, nuts",
            "chapter_url": "https://example.com", "table_caption": "Tomato preparations",
            "reference_number": "2002.10.00", "subheading": "- Tomatoes, whole or in pieces",
            "indent_level": 1, "statistical_code": "10", "unit": "kg", "rate": "5%", "tco_text": "", "tco_href": ""
        },
        
        # Section XVI - Machinery/Electronics
        {
            "section": "XVI", "chapter_number": "84", "chapter_title": "Machinery and mechanical appliances",
            "chapter_url": "https://example.com", "table_caption": "Excavating machinery",
            "reference_number": "8429", "subheading": "SELF-PROPELLED BULLDOZERS, ANGLEDOZERS, GRADERS, LEVELLERS, SCRAPERS, MECHANICAL SHOVELS, EXCAVATORS, SHOVEL LOADERS, TAMPING MACHINES AND ROAD ROLLERS:",
            "indent_level": 0, "statistical_code": "", "unit": "", "rate": "", "tco_text": "", "tco_href": ""
        },
        {
            "section": "XVI", "chapter_number": "84", "chapter_title": "Machinery and mechanical appliances",
            "chapter_url": "https://example.com", "table_caption": "Excavating machinery",
            "reference_number": "8429.51.00", "subheading": "-- Front-end shovel loaders",
            "indent_level": 1, "statistical_code": "51", "unit": "No", "rate": "5%", "tco_text": "", "tco_href": ""
        },
        {
            "section": "XVI", "chapter_number": "85", "chapter_title": "Electrical machinery and equipment",
            "chapter_url": "https://example.com", "table_caption": "Electric motors",
            "reference_number": "8501", "subheading": "ELECTRIC MOTORS AND GENERATORS (EXCLUDING GENERATING SETS):",
            "indent_level": 0, "statistical_code": "", "unit": "", "rate": "", "tco_text": "", "tco_href": ""
        },
        {
            "section": "XVI", "chapter_number": "85", "chapter_title": "Electrical machinery and equipment",
            "chapter_url": "https://example.com", "table_caption": "Electric motors",
            "reference_number": "8501.10.00", "subheading": "- Motors of an output not exceeding 37.5 W",
            "indent_level": 1, "statistical_code": "10", "unit": "No", "rate": "Free", "tco_text": "", "tco_href": ""
        },
        
        # Section XI - Textiles
        {
            "section": "XI", "chapter_number": "61", "chapter_title": "Articles of apparel and clothing accessories, knitted or crocheted",
            "chapter_url": "https://example.com", "table_caption": "Men's or boys' suits, ensembles, jackets, blazers, trousers",
            "reference_number": "6103", "subheading": "MEN'S OR BOYS' SUITS, ENSEMBLES, JACKETS, BLAZERS, TROUSERS, BIB AND BRACE OVERALLS, BREECHES AND SHORTS (OTHER THAN SWIMWEAR), KNITTED OR CROCHETED:",
            "indent_level": 0, "statistical_code": "", "unit": "", "rate": "", "tco_text": "", "tco_href": ""
        },
        {
            "section": "XI", "chapter_number": "61", "chapter_title": "Articles of apparel and clothing accessories, knitted or crocheted",
            "chapter_url": "https://example.com", "table_caption": "Men's or boys' suits, ensembles, jackets, blazers, trousers",
            "reference_number": "6103.10.00", "subheading": "- Suits",
            "indent_level": 1, "statistical_code": "10", "unit": "No", "rate": "10%", "tco_text": "", "tco_href": ""
        },
        
        # Section XVII - Transport
        {
            "section": "XVII", "chapter_number": "87", "chapter_title": "Vehicles other than railway or tramway rolling-stock",
            "chapter_url": "https://example.com", "table_caption": "Motor cars and other motor vehicles",
            "reference_number": "8703", "subheading": "MOTOR CARS AND OTHER MOTOR VEHICLES PRINCIPALLY DESIGNED FOR THE TRANSPORT OF PERSONS:",
            "indent_level": 0, "statistical_code": "", "unit": "", "rate": "", "tco_text": "", "tco_href": ""
        },
        {
            "section": "XVII", "chapter_number": "87", "chapter_title": "Vehicles other than railway or tramway rolling-stock",
            "chapter_url": "https://example.com", "table_caption": "Motor cars and other motor vehicles",
            "reference_number": "8703.10.00", "subheading": "- Vehicles specially designed for travelling on snow; golf cars and similar vehicles",
            "indent_level": 1, "statistical_code": "10", "unit": "No", "rate": "5%", "tco_text": "", "tco_href": ""
        }
    ]
    
    return test_data

def save_test_data_to_file(data: List[Dict], filename: str = "test_tariff_data.jsonl"):
    """Save test data to JSON lines file"""
    with open(filename, 'w', encoding='utf-8') as f:
        for entry in data:
            f.write(json.dumps(entry) + '\n')
    print(f"Saved {len(data)} entries to {filename}")

async def demonstrate_classification_examples():
    """Demonstrate various classification examples"""
    
    # Test cases with expected sections
    test_cases = [
        ("live breeding horses for racing", "Animals"),
        ("asses", "Animals"), 
        ("buffalo", "Animals"),
    ]
    
    print("=== TARIFF CLASSIFICATION EXAMPLES ===\n")
    
    # Create and load test data
    test_data = create_comprehensive_test_data()
    save_test_data_to_file(test_data)
    
    # Initialize classifier
    print("Initializing tariff classifier...")
    classifier = TariffClassifier("test_tariff_data.jsonl")
    
    # Set custom confidence thresholds
    custom_thresholds = {
        "sections": 0.40,
        "chapters": 0.35,
        "headings": 0.30,
        "subheadings": 0.25
    }
    classifier.set_confidence_thresholds(custom_thresholds)
    
    # Initialize base embeddings
    print("Initializing base embeddings (this may take a moment)...")
    await classifier.initialize_base_embeddings()
    
    # Display structure summary
    print("\n=== TARIFF STRUCTURE SUMMARY ===")
    structure = classifier.get_tariff_structure_summary()
    for key, value in structure.items():
        print(f"{key}: {value}")
    
    print(f"\n=== CLASSIFICATION EXAMPLES ===\n")
    
    for i, (text, expected_section) in enumerate(test_cases, 1):
        print(f"\n--- Example {i}: {text} ---")
        print(f"Expected Section: {expected_section} ({SECTION_MAP.get(expected_section, 'Unknown')})")
        
        try:
            # Perform hierarchical classification
            result = await classifier.classify_hierarchical(
                text, 
                max_depth=4,
                include_tariff_details=True,
                strict_mode=False  # Allow classification to continue even with low confidence
            )
            
            print(f"Processing Time: {result.processing_time_ms:.2f}ms")
            print(f"Full Classification Code: {result.full_code}")
            
            if result.classification_stopped:
                print(f"⚠️  Classification stopped: {result.stop_reason}")
            
            # Display classification path
            for j, classification in enumerate(result.classification_path):
                level_name = classification.level.value.title()
                confidence = classification.confidence_score
                meets_threshold = "✓" if classification.meets_threshold else "⚠️"
                
                print(f"  {level_name}: {classification.predicted_label}")
                print(f"    Code: {classification.label_code}")
                print(f"    Confidence: {confidence:.4f} {meets_threshold}")
                
                # Show top 3 alternatives for context
                if len(classification.all_scores) > 1:
                    sorted_scores = sorted(classification.all_scores.items(), 
                                         key=lambda x: x[1], reverse=True)[:3]
                    print(f"    Top alternatives:")
                    for alt_label, alt_score in sorted_scores:
                        marker = "→" if alt_label == classification.predicted_label else " "
                        print(f"      {marker} {alt_label}: {alt_score:.4f}")
            
            # Display final tariff entry if available
            if result.final_tariff_entry:
                entry = result.final_tariff_entry
                print(f"\n  📋 Final Tariff Details:")
                print(f"    Reference: {entry.reference_number}")
                print(f"    Description: {entry.subheading.strip('- ')}")
                print(f"    Unit: {entry.unit}")
                print(f"    Rate: {entry.rate}")
                print(f"    Statistical Code: {entry.statistical_code}")
            
            # Check if prediction matches expectation
            if result.classification_path:
                predicted_section = result.classification_path[0].predicted_label
                section_match = expected_section in predicted_section or predicted_section in expected_section
                print(f"\n  ✅ Section Match: {'YES' if section_match else 'NO'}")
            
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
    
    print(f"\n=== SEARCH FUNCTIONALITY ===\n")
    
    # Demonstrate search functionality
    search_terms = ["horse", "motor", "tomato", "excavator"]
    for term in search_terms:
        print(f"Searching for '{term}':")
        results = classifier.search_tariff_entries(term, max_results=3)
        for result in results:
            print(f"  • {result.reference_number}: {result.subheading.strip('- ')}")
        print()
    
    print(f"\n=== CACHE STATUS ===\n")
    
    # Show cache status
    cache_status = classifier.get_cache_status()
    for classifier_id, status in cache_status.items():
        print(f"{classifier_id}:")
        for key, value in status.items():
            print(f"  {key}: {value}")
        print()

async def demonstrate_single_level_classification():
    """Demonstrate single-level classification"""
    print("\n=== SINGLE LEVEL CLASSIFICATION EXAMPLES ===\n")
    
    test_data = create_comprehensive_test_data()
    save_test_data_to_file(test_data)
    
    classifier = TariffClassifier("test_tariff_data.jsonl")
    await classifier.initialize_base_embeddings()
    
    # Test section-level classification
    print("Section-level classification:")
    test_texts = [
        "live cattle for breeding",
        "industrial machinery",
        "cotton fabric",
        "passenger vehicle"
    ]
    
    for text in test_texts:
        result = await classifier.classify_single_level(text, ClassificationLevel.SECTIONS)
        print(f"  '{text}' → {result.predicted_label} (confidence: {result.confidence_score:.4f})")
    
    # Test chapter-level classification within a section
    print(f"\nChapter-level classification within Section I (Animals):")
    chapter_texts = [
        "live horses",
        "fresh beef meat"
    ]
    
    for text in chapter_texts:
        result = await classifier.classify_single_level(
            text, 
            ClassificationLevel.CHAPTERS, 
            parent_path=["I"]
        )
        print(f"  '{text}' → {result.predicted_label} (confidence: {result.confidence_score:.4f})")

def demonstrate_section_mapping():
    """Demonstrate the section mapping functionality"""
    print("\n=== SECTION MAPPING ===\n")
    
    print("Available Tariff Sections:")
    for description, code in SECTION_MAP.items():
        print(f"  Section {code.rjust(4)}: {description}")
    
    print(f"\nTotal Sections: {len(SECTION_MAP)}")
    
    # Reverse mapping for code lookup
    reverse_map = {v: k for k, v in SECTION_MAP.items()}
    print(f"\nReverse lookup examples:")
    for code in ["I", "XVI", "XI", "XVII"]:
        description = reverse_map.get(code, "Unknown")
        print(f"  Section {code}: {description}")

async def main():
    """Main example usage function"""
    print("🚀 TARIFF CLASSIFICATION SYSTEM DEMO")
    print("=" * 50)
    
    try:
        # Demonstrate section mapping
        demonstrate_section_mapping()
        
        # Run comprehensive classification examples
        await demonstrate_classification_examples()
        
        # Run single-level classification examples
        await demonstrate_single_level_classification()
        
        print("\n" + "=" * 50)
        print("✅ Demo completed successfully!")
        print("\nKey Features Demonstrated:")
        print("  • Hierarchical tariff classification")
        print("  • Confidence threshold validation")
        print("  • Multi-level semantic matching")
        print("  • Embedding cache management")
        print("  • Search functionality")
        print("  • Comprehensive error handling")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

# Additional utility functions for advanced usage
async def benchmark_classification_speed():
    """Benchmark classification speed"""
    print("\n=== PERFORMANCE BENCHMARK ===\n")
    
    test_data = create_comprehensive_test_data()
    save_test_data_to_file(test_data)
    
    classifier = TariffClassifier("test_tariff_data.jsonl")
    await classifier.initialize_base_embeddings()
    
    test_items = [
        "live horses for racing",
        "excavator machinery", 
        "cotton shirts",
        "passenger cars",
        "electronic devices"
    ]
    
    import time
    total_time = 0
    
    for item in test_items:
        start = time.time()
        result = await classifier.classify_hierarchical(item, max_depth=2)
        end = time.time()
        
        processing_time = (end - start) * 1000
        total_time += processing_time
        
        print(f"'{item}': {processing_time:.2f}ms → {result.full_code}")
    
    avg_time = total_time / len(test_items)
    print(f"\nAverage classification time: {avg_time:.2f}ms")
    print(f"Total time: {total_time:.2f}ms")

if __name__ == "__main__":
    # Run the main example
    asyncio.run(main())
    
    # Optionally run benchmark
    # asyncio.run(benchmark_classification_speed())