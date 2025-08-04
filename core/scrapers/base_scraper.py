import time
import random
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class BaseScraper(ABC):
    """
    Base class for all web scrapers.
    Provides common functionality for respectful web scraping.
    """
    
    def __init__(self, name: str, base_delay: float = 1.0, max_delay: float = 5.0):
        self.name = name
        self.base_delay = base_delay
        self.max_delay = max_delay
        
        # Set up logging
        self.logger = logging.getLogger(f"Scraper.{name}")
        
        # Set up session with retries and proper headers
        self.session = requests.Session()
        self.setup_session()
        
        # Rate limiting
        self.last_request_time = 0
        self.request_count = 0
        
        # Statistics
        self.stats = {
            'requests_made': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'data_points_collected': 0,
            'start_time': datetime.utcnow().isoformat()
        }
        
        self.logger.info(f"Scraper {name} initialized")
    
    def setup_session(self):
        """Set up the requests session with proper configuration"""
        # Retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set reasonable headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    @abstractmethod
    def scrape_data(self, target: str, **kwargs) -> Dict[str, Any]:
        """
        Scrape data from the target.
        Must be implemented by each scraper type.
        """
        pass
    
    @abstractmethod
    def parse_response(self, response: requests.Response, **kwargs) -> Dict[str, Any]:
        """
        Parse the response from a request.
        Must be implemented by each scraper type.
        """
        pass
    
    def make_request(self, url: str, method: str = 'GET', **kwargs) -> Optional[requests.Response]:
        """Make a rate-limited request"""
        # Implement rate limiting
        self.respect_rate_limit()
        
        try:
            self.stats['requests_made'] += 1
            
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            
            self.stats['successful_requests'] += 1
            self.logger.debug(f"Successful request to {url}")
            
            return response
            
        except requests.exceptions.RequestException as e:
            self.stats['failed_requests'] += 1
            self.logger.error(f"Request failed for {url}: {str(e)}")
            return None
    
    def respect_rate_limit(self):
        """Implement respectful rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        # Calculate delay with some randomization
        delay = self.base_delay + random.uniform(0, self.max_delay - self.base_delay)
        
        # If we haven't waited long enough, sleep
        if time_since_last < delay:
            sleep_time = delay - time_since_last
            self.logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    def extract_text_safely(self, element, default: str = "") -> str:
        """Safely extract text from a BeautifulSoup element"""
        try:
            return element.get_text(strip=True) if element else default
        except Exception:
            return default
    
    def extract_attribute_safely(self, element, attribute: str, default: str = "") -> str:
        """Safely extract an attribute from a BeautifulSoup element"""
        try:
            return element.get(attribute, default) if element else default
        except Exception:
            return default
    
    def clean_price(self, price_text: str) -> Optional[float]:
        """Clean and extract price from text"""
        if not price_text:
            return None
        
        try:
            # Remove common currency symbols and text
            import re
            cleaned = re.sub(r'[^\\d.,]', '', price_text)
            cleaned = cleaned.replace(',', '')
            
            if cleaned:
                return float(cleaned)
        except (ValueError, AttributeError):
            pass
        
        return None
    
    def validate_data(self, data: Dict[str, Any], required_fields: List[str]) -> bool:
        """Validate that scraped data contains required fields"""
        for field in required_fields:
            if field not in data or not data[field]:
                self.logger.warning(f"Missing required field: {field}")
                return False
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get scraper statistics"""
        current_stats = self.stats.copy()
        current_stats['success_rate'] = (
            self.stats['successful_requests'] / max(self.stats['requests_made'], 1)
        ) * 100
        current_stats['current_time'] = datetime.utcnow().isoformat()
        
        return current_stats
    
    def reset_statistics(self):
        """Reset scraper statistics"""
        self.stats = {
            'requests_made': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'data_points_collected': 0,
            'start_time': datetime.utcnow().isoformat()
        }
        
        self.logger.info("Statistics reset")
    
    def shutdown(self):
        """Gracefully shutdown the scraper"""
        self.logger.info(f"Shutting down scraper {self.name}")
        
        if self.session:
            self.session.close()
        
        # Log final statistics
        final_stats = self.get_statistics()
        self.logger.info(f"Final statistics: {final_stats}")

class AmazonScraper(BaseScraper):
    """Scraper for Amazon product data"""
    
    def __init__(self):
        super().__init__("Amazon", base_delay=2.0, max_delay=5.0)
        
        # Amazon-specific headers
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        })
    
    def scrape_data(self, product_url: str, **kwargs) -> Dict[str, Any]:
        """Scrape Amazon product data"""
        response = self.make_request(product_url)
        
        if not response:
            return {'error': 'Failed to fetch product page'}
        
        return self.parse_response(response, **kwargs)
    
    def parse_response(self, response: requests.Response, **kwargs) -> Dict[str, Any]:
        """Parse Amazon product page"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract product information
            product_data = {
                'title': self.extract_product_title(soup),
                'price': self.extract_product_price(soup),
                'rating': self.extract_product_rating(soup),
                'review_count': self.extract_review_count(soup),
                'availability': self.extract_availability(soup),
                'images': self.extract_product_images(soup),
                'description': self.extract_product_description(soup),
                'scraped_at': datetime.utcnow().isoformat()
            }
            
            # Validate required fields
            if self.validate_data(product_data, ['title']):
                self.stats['data_points_collected'] += 1
                return {'status': 'success', 'data': product_data}
            else:
                return {'status': 'error', 'error': 'Invalid product data'}
                
        except Exception as e:
            self.logger.error(f"Error parsing Amazon response: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def extract_product_title(self, soup) -> str:
        """Extract product title from Amazon page"""
        selectors = [
            '#productTitle',
            '.product-title',
            'h1.a-size-large'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return self.extract_text_safely(element)
        
        return ""
    
    def extract_product_price(self, soup) -> Optional[float]:
        """Extract product price from Amazon page"""
        price_selectors = [
            '.a-price-whole',
            '.a-offscreen',
            '#priceblock_dealprice',
            '#priceblock_ourprice'
        ]
        
        for selector in price_selectors:
            element = soup.select_one(selector)
            if element:
                price_text = self.extract_text_safely(element)
                price = self.clean_price(price_text)
                if price:
                    return price
        
        return None
    
    def extract_product_rating(self, soup) -> Optional[float]:
        """Extract product rating from Amazon page"""
        rating_element = soup.select_one('.a-icon-alt')
        if rating_element:
            rating_text = self.extract_text_safely(rating_element)
            try:
                # Extract rating from text like "4.5 out of 5 stars"
                import re
                match = re.search(r'(\\d+\\.\\d+)', rating_text)
                if match:
                    return float(match.group(1))
            except (ValueError, AttributeError):
                pass
        
        return None
    
    def extract_review_count(self, soup) -> Optional[int]:
        """Extract review count from Amazon page"""
        review_selectors = [
            '#acrCustomerReviewText',
            '.a-link-normal'
        ]
        
        for selector in review_selectors:
            element = soup.select_one(selector)
            if element:
                review_text = self.extract_text_safely(element)
                try:
                    # Extract number from text like "1,234 ratings"
                    import re
                    match = re.search(r'([\\d,]+)', review_text)
                    if match:
                        return int(match.group(1).replace(',', ''))
                except (ValueError, AttributeError):
                    pass
        
        return None
    
    def extract_availability(self, soup) -> str:
        """Extract product availability from Amazon page"""
        availability_selectors = [
            '#availability span',
            '.a-color-success',
            '.a-color-state'
        ]
        
        for selector in availability_selectors:
            element = soup.select_one(selector)
            if element:
                availability = self.extract_text_safely(element)
                if availability:
                    return availability
        
        return "Unknown"
    
    def extract_product_images(self, soup) -> List[str]:
        """Extract product images from Amazon page"""
        images = []
        
        # Main product image
        main_image = soup.select_one('#landingImage')
        if main_image:
            src = self.extract_attribute_safely(main_image, 'src')
            if src:
                images.append(src)
        
        # Additional images
        additional_images = soup.select('.a-button-thumbnail img')
        for img in additional_images[:5]:  # Limit to 5 additional images
            src = self.extract_attribute_safely(img, 'src')
            if src and src not in images:
                images.append(src)
        
        return images
    
    def extract_product_description(self, soup) -> str:
        """Extract product description from Amazon page"""
        description_selectors = [
            '#feature-bullets ul',
            '#productDescription',
            '.a-unordered-list'
        ]
        
        for selector in description_selectors:
            element = soup.select_one(selector)
            if element:
                description = self.extract_text_safely(element)
                if description:
                    return description[:1000]  # Limit description length
        
        return ""