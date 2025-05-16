import logging
import re
from PIL import Image
import docx2txt
import fitz  # PyMuPDF
import xml.etree.ElementTree as ET
from collections import Counter
import json

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Loader:
    def __init__(self):
        self.logger = logger

    def text_to_vector(self, text):
        self.logger.debug("Converting text to Bag-of-Words vector")
        try:
            if not text or not text.strip():
                self.logger.warning("Text is empty or contains only whitespace")
                return []
            
            # Simple text preprocessing: lowercase, remove punctuation, split into words
            words = re.findall(r'\b\w+\b', text.lower())
            if not words:
                self.logger.warning("No valid words found after preprocessing")
                return []
            
            # Create a vocabulary of the top 100 most frequent words
            word_counts = Counter(words)
            top_words = [word for word, _ in word_counts.most_common(100)]
            if not top_words:
                self.logger.warning("No top words identified after counting")
                return []
            
            # Create a vector: frequency of each top word in the text
            vector = [word_counts[word] for word in top_words]
            self.logger.debug(f"Generated vector with length {len(vector)}")
            return vector
        
        except Exception as e:
            self.logger.error(f"Failed to convert text to vector: {str(e)}")
            return []

    def image_to_vector(self, img):
        self.logger.debug("Converting image to color histogram vector")
        try:
            # Ensure image is in RGB mode
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Get the color histogram (256 bins per channel for R, G, B)
            histogram = img.histogram()
            if len(histogram) != 768:
                self.logger.warning("Unexpected histogram length, expected 768 values")
                return []
            
            # Normalize the histogram to reduce the impact of image size
            total_pixels = img.width * img.height
            if total_pixels == 0:
                self.logger.warning("Image has zero pixels")
                return []
            
            normalized_histogram = [value / total_pixels for value in histogram]
            self.logger.debug(f"Generated image vector with length {len(normalized_histogram)}")
            return normalized_histogram
        except Exception as e:
            self.logger.error(f"Failed to convert image to vector: {str(e)}")
            return []

    def load_image(self, filepath):
        try:
            img = Image.open(filepath)
            metadata = {
                'format': img.format,
                'size': img.size,
                'mode': img.mode
            }
            vector = self.image_to_vector(img)
            return metadata, vector
        except Exception as e:
            self.logger.error(f"Error loading image: {e}")
            return {'error': str(e)}, []

    def load_docx(self, filepath):
        try:
            text = docx2txt.process(filepath)
            words = re.findall(r'\b\w+\b', text.lower())
            metadata = {
                'text_length': len(text),
                'word_count': len(words)
            }
            vector = self.text_to_vector(text)
            return metadata, vector
        except Exception as e:
            self.logger.error(f"Error loading DOCX: {e}")
            return {'error': str(e)}, []

    def load_pdf(self, filepath):
        try:
            doc = fitz.open(filepath)
            metadata = {
                'page_count': doc.page_count,
                'title': doc.metadata.get('title', '') if doc.metadata else ''
            }
            text = ''
            for page in doc:
                text += page.get_text() or ''
            doc.close()
            vector = self.text_to_vector(text)
            return metadata, vector
        except Exception as e:
            self.logger.error(f"Error loading PDF: {e}")
            return {'error': str(e)}, []

    def load_svg(self, filepath):
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            metadata = {
                'width': root.get('width', 'unknown'),
                'height': root.get('height', 'unknown'),
                'namespace': root.tag.split('}')[0][1:] if '}' in root.tag else 'unknown'
            }
            return metadata, []  # No vector for SVG
        except Exception as e:
            self.logger.error(f"Error loading SVG: {e}")
            return {'error': str(e)}, []