import logging
import json
import requests
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import torch

# Download required NLTK data
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)

logger = logging.getLogger(__name__)

class NLPService:
    """
    Service for handling NLP-related tasks such as text summarization and category classification.
    Uses a pre-trained sentence transformer model for generating embeddings.
    """
    
    def __init__(self, model_name: str = None):
        """
        Initialize the NLP service with a pre-trained model.
        
        Args:
            model_name: Name of the pre-trained model to use (defaults to settings.NLP_MODEL_NAME)
        """
        self.model_name = model_name or getattr(settings, 'NLP_MODEL_NAME', 'sentence-transformers/all-mpnet-base-v2')
        self.model = self._load_model()
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        self.similarity_threshold = getattr(settings, 'SIMILARITY_THRESHOLD', 0.75)
        
        # Define category labels and their associated keywords
        self.categories = {
            'technology': ['technology', 'tech', 'computer', 'software', 'hardware', 'ai', 'artificial intelligence', 'machine learning', 'data'],
            'business': ['business', 'economy', 'market', 'finance', 'stock', 'investment', 'company', 'industry'],
            'sports': ['sports', 'football', 'basketball', 'soccer', 'tennis', 'golf', 'olympics', 'game', 'match', 'tournament'],
            'entertainment': ['entertainment', 'movie', 'film', 'tv', 'television', 'celebrity', 'actor', 'actress', 'music', 'song', 'album'],
            'health': ['health', 'medical', 'medicine', 'disease', 'hospital', 'doctor', 'patient', 'fitness', 'wellness'],
            'science': ['science', 'research', 'study', 'scientist', 'discovery', 'physics', 'biology', 'chemistry', 'space'],
            'politics': ['politics', 'government', 'election', 'president', 'congress', 'senate', 'democrat', 'republican'],
            'general': ['news', 'update', 'world', 'today', 'latest', 'breaking']
        }
    
    def _load_model(self):
        """
        Load the pre-trained sentence transformer model.
        Uses caching to avoid reloading the model on each request.
        """
        cache_key = f"nlp_model_{self.model_name.replace('/', '_')}"
        model = cache.get(cache_key)
        
        if model is None:
            try:
                logger.info(f"Loading NLP model: {self.model_name}")
                model = SentenceTransformer(self.model_name)
                # Cache the model for 24 hours
                cache.set(cache_key, model, timeout=60*60*24)
            except Exception as e:
                logger.error(f"Error loading NLP model: {str(e)}")
                raise
                
        return model
    
    def preprocess_text(self, text: str) -> str:
        """
        Preprocess text by lowercasing, removing stopwords, and lemmatizing.
        
        Args:
            text: Input text to preprocess
            
        Returns:
            Preprocessed text
        """
        if not text:
            return ""
            
        # Tokenize and process each word
        words = text.lower().split()
        words = [self.lemmatizer.lemmatize(word) for word in words if word.isalnum() and word not in self.stop_words]
        
        return ' '.join(words)
    
    def generate_summary(self, text: str, num_sentences: int = 3) -> str:
        """
        Generate a summary of the input text using extractive summarization.
        
        Args:
            text: Input text to summarize
            num_sentences: Number of sentences in the summary
            
        Returns:
            Generated summary
        """
        if not text:
            return ""
            
        try:
            # Tokenize the text into sentences
            sentences = sent_tokenize(text)
            
            # If text is too short, return as is
            if len(sentences) <= num_sentences:
                return ' '.join(sentences)
                
            # Generate sentence embeddings
            sentence_embeddings = self.model.encode(sentences, convert_to_tensor=True)
            
            # Calculate similarity matrix
            similarity_matrix = cosine_similarity(
                sentence_embeddings.cpu().numpy(),
                sentence_embeddings.cpu().numpy()
            )
            
            # Convert to similarity graph and calculate sentence scores
            scores = np.zeros(len(sentences))
            for i in range(len(sentences)):
                for j in range(len(sentences)):
                    if i != j:
                        scores[i] += similarity_matrix[i][j]
            
            # Get top N sentences
            top_sentences_idx = np.argsort(scores)[-num_sentences:]
            top_sentences = [sentences[i] for i in sorted(top_sentences_idx)]
            
            return ' '.join(top_sentences)
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            # Fallback: return first few sentences
            return ' '.join(sentences[:num_sentences])
    
    def classify_category(self, title: str, description: str = "") -> str:
        """
        Classify an article into one of the predefined categories.
        
        Args:
            title: Article title
            description: Article description (optional)
            
        Returns:
            Predicted category
        """
        if not title:
            return 'general'
            
        try:
            # Preprocess text
            text = f"{title} {description}".lower()
            
            # Simple keyword-based classification
            category_scores = {category: 0 for category in self.categories}
            
            for category, keywords in self.categories.items():
                for keyword in keywords:
                    if keyword in text:
                        category_scores[category] += 1
            
            # Get category with highest score
            predicted_category = max(category_scores.items(), key=lambda x: x[1])[0]
            
            # If no keywords matched, use ML-based classification
            if category_scores[predicted_category] == 0:
                predicted_category = self._classify_with_ml(text)
                
            return predicted_category
            
        except Exception as e:
            logger.error(f"Error in category classification: {str(e)}")
            return 'general'
    
    def _classify_with_ml(self, text: str) -> str:
        """
        Classify text using a machine learning model.
        
        Args:
            text: Input text to classify
            
        Returns:
            Predicted category
        """
        try:
            # Generate text embedding
            embedding = self.model.encode(text, convert_to_tensor=True).unsqueeze(0)
            
            # Get category embeddings (pre-computed)
            category_embeddings = self._get_category_embeddings()
            
            # Calculate similarity with each category
            similarities = cosine_similarity(
                embedding.cpu().numpy(),
                category_embeddings.cpu().numpy()
            )[0]
            
            # Get most similar category
            max_idx = np.argmax(similarities)
            categories = list(self.categories.keys())
            
            # Only return if similarity is above threshold, else 'general'
            if similarities[max_idx] >= self.similarity_threshold:
                return categories[max_idx]
            return 'general'
            
        except Exception as e:
            logger.error(f"Error in ML-based classification: {str(e)}")
            return 'general'
    
    def _get_category_embeddings(self):
        """
        Get or compute embeddings for each category based on their keywords.
        """
        cache_key = "category_embeddings"
        embeddings = cache.get(cache_key)
        
        if embeddings is None:
            # Create a representative text for each category
            category_texts = [
                f"This is a {category} article about {', '.join(keywords)}."
                for category, keywords in self.categories.items()
            ]
            
            # Generate embeddings
            embeddings = self.model.encode(category_texts, convert_to_tensor=True)
            
            # Cache for 24 hours
            cache.set(cache_key, embeddings, timeout=60*60*24)
            
        return embeddings


class NewsAPIService:
    """
    Service for interacting with the NewsAPI.
    Handles fetching articles, pagination, and error handling.
    """
    
    BASE_URL = "https://newsapi.org/v2"
    
    def __init__(self, api_key: str = None):
        """
        Initialize the NewsAPI service.
        
        Args:
            api_key: NewsAPI key (defaults to settings.NEWS_API_KEY)
        """
        self.api_key = api_key or getattr(settings, 'NEWS_API_KEY', '')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'NewsHub/1.0',
            'Accept': 'application/json'
        })
    
    def fetch_articles(self, query: str = None, category: str = None, 
                      page_size: int = 20, page: int = 1) -> List[Dict]:
        """
        Fetch articles from NewsAPI.
        
        Args:
            query: Search query
            category: News category (e.g., 'technology', 'business')
            page_size: Number of results per page (1-100)
            page: Page number
            
        Returns:
            List of article dictionaries
        """
        if not self.api_key:
            logger.error("NewsAPI key not configured")
            return []
            
        try:
            # Build request URL
            if query:
                endpoint = f"{self.BASE_URL}/everything"
                params = {
                    'q': query,
                    'pageSize': min(page_size, 100),
                    'page': page,
                    'sortBy': 'publishedAt',
                    'language': 'en',
                    'apiKey': self.api_key
                }
            else:
                endpoint = f"{self.BASE_URL}/top-headlines"
                params = {
                    'category': category or 'general',
                    'country': 'us',
                    'pageSize': min(page_size, 100),
                    'page': page,
                    'apiKey': self.api_key
                }
            
            # Make the request
            response = self.session.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            if data.get('status') != 'ok':
                logger.error(f"NewsAPI error: {data.get('message', 'Unknown error')}")
                return []
                
            return data.get('articles', [])
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching articles from NewsAPI: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in fetch_articles: {str(e)}")
            return []
    
    def get_sources(self, category: str = None, language: str = 'en') -> List[Dict]:
        """
        Get available news sources.
        
        Args:
            category: Filter by category
            language: Filter by language (ISO 639-1 code)
            
        Returns:
            List of source dictionaries
        """
        if not self.api_key:
            logger.error("NewsAPI key not configured")
            return []
            
        try:
            # Build request URL
            endpoint = f"{self.BASE_URL}/sources"
            params = {
                'apiKey': self.api_key,
                'language': language
            }
            
            if category:
                params['category'] = category
            
            # Make the request
            response = self.session.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            if data.get('status') != 'ok':
                logger.error(f"NewsAPI error: {data.get('message', 'Unknown error')}")
                return []
                
            return data.get('sources', [])
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching sources from NewsAPI: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_sources: {str(e)}")
            return []


# Initialize global instances
nlp_service = NLPService()
news_api_service = NewsAPIService()