import requests
import logging
import json
from src.config import Config

class WordPressService:
    """Service for interacting with WordPress REST API."""
    
    def __init__(self):
        """Initialize WordPress service with configuration."""
        self.api_url = Config.WORDPRESS_API_URL
        self.username = Config.WORDPRESS_USERNAME
        self.password = Config.WORDPRESS_PASSWORD
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Validate configuration
        if not all([self.api_url, self.username, self.password]):
            self.logger.warning("WordPress configuration is incomplete. Some features may not work.")
    
    def post_article(self, article):
        """
        Post an article to WordPress.
        
        Args:
            article: Article model instance
            
        Returns:
            dict: Response data including WordPress post ID if successful
        """
        self.logger.info(f"Posting article '{article.title}' to WordPress")
        
        # Prepare post data
        post_data = {
            'title': article.title,
            'content': article.content,
            'status': 'publish',  # Can be: publish, future, draft, pending, private
            'excerpt': article.meta_description,
        }
        
        # Handle tags if available
        if article.keywords:
            keywords = json.loads(article.keywords) if isinstance(article.keywords, str) else article.keywords
            if keywords:
                # Get tag IDs for the first few keywords
                tag_ids = self._get_or_create_tags(keywords[:5])
                if tag_ids:
                    post_data['tags'] = tag_ids
        
        try:
            # Make API request to create post
            # Note: WordPress application passwords may contain spaces
            # which need to be preserved for authentication
            self.logger.info(f"Making request to WordPress API: {self.api_url}/posts")
            self.logger.info(f"Post data: {post_data}")
            
            response = requests.post(
                f"{self.api_url}/posts",
                json=post_data,
                auth=(self.username, self.password),
                headers={'Content-Type': 'application/json'}
            )
            
            # Log response details for debugging
            self.logger.info(f"WordPress API response status: {response.status_code}")
            self.logger.info(f"WordPress API response headers: {response.headers}")
            
            # For error responses, log the response content
            if response.status_code >= 400:
                self.logger.error(f"WordPress API error response: {response.text}")
            
            # Check if request was successful
            response.raise_for_status()
            
            # Parse response
            response_data = response.json()
            
            self.logger.info(f"Article posted successfully to WordPress with ID: {response_data.get('id')}")
            
            return {
                'success': True,
                'wordpress_post_id': response_data.get('id'),
                'wordpress_url': response_data.get('link'),
                'response': response_data
            }
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to post article to WordPress: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_article(self, article):
        """
        Update an existing article on WordPress.
        
        Args:
            article: Article model instance with wordpress_post_id
            
        Returns:
            dict: Response data
        """
        if not article.wordpress_post_id:
            self.logger.error("Cannot update article: No WordPress post ID")
            return {
                'success': False,
                'error': 'No WordPress post ID'
            }
        
        self.logger.info(f"Updating article '{article.title}' on WordPress (ID: {article.wordpress_post_id})")
        
        # Prepare post data
        post_data = {
            'title': article.title,
            'content': article.content,
            'excerpt': article.meta_description,
        }
        
        try:
            # Make API request to update post
            self.logger.info(f"Making request to update post on WordPress API: {self.api_url}/posts/{article.wordpress_post_id}")
            self.logger.info(f"Update data: {post_data}")
            
            response = requests.post(
                f"{self.api_url}/posts/{article.wordpress_post_id}",
                json=post_data,
                auth=(self.username, self.password),
                headers={'Content-Type': 'application/json'}
            )
            
            # Log response details for debugging
            self.logger.info(f"WordPress API update response status: {response.status_code}")
            
            # For error responses, log the response content
            if response.status_code >= 400:
                self.logger.error(f"WordPress API update error response: {response.text}")
            
            # Check if request was successful
            response.raise_for_status()
            
            # Parse response
            response_data = response.json()
            
            self.logger.info(f"Article updated successfully on WordPress")
            
            return {
                'success': True,
                'wordpress_url': response_data.get('link'),
                'response': response_data
            }
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to update article on WordPress: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_article(self, wordpress_post_id):
        """
        Delete an article from WordPress.
        
        Args:
            wordpress_post_id: ID of the WordPress post
            
        Returns:
            dict: Response data
        """
        if not wordpress_post_id:
            self.logger.error("Cannot delete article: No WordPress post ID")
            return {
                'success': False,
                'error': 'No WordPress post ID'
            }
        
        self.logger.info(f"Deleting article from WordPress (ID: {wordpress_post_id})")
        
        try:
            # Make API request to delete post
            self.logger.info(f"Making request to delete post on WordPress API: {self.api_url}/posts/{wordpress_post_id}")
            
            response = requests.delete(
                f"{self.api_url}/posts/{wordpress_post_id}",
                auth=(self.username, self.password),
                params={'force': True}  # Permanently delete instead of moving to trash
            )
            
            # Log response details for debugging
            self.logger.info(f"WordPress API delete response status: {response.status_code}")
            
            # For error responses, log the response content
            if response.status_code >= 400:
                self.logger.error(f"WordPress API delete error response: {response.text}")
            
            # Check if request was successful
            response.raise_for_status()
            
            self.logger.info(f"Article deleted successfully from WordPress")
            
            return {
                'success': True
            }
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to delete article from WordPress: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_article(self, wordpress_post_id):
        """
        Get article details from WordPress.
        
        Args:
            wordpress_post_id: ID of the WordPress post
            
        Returns:
            dict: Article data from WordPress
        """
        if not wordpress_post_id:
            self.logger.error("Cannot get article: No WordPress post ID")
            return {
                'success': False,
                'error': 'No WordPress post ID'
            }
        
        self.logger.info(f"Getting article from WordPress (ID: {wordpress_post_id})")
        
        try:
            # Make API request to get post
            self.logger.info(f"Making request to get post from WordPress API: {self.api_url}/posts/{wordpress_post_id}")
            
            response = requests.get(
                f"{self.api_url}/posts/{wordpress_post_id}",
                auth=(self.username, self.password)
            )
            
            # Log response details for debugging
            self.logger.info(f"WordPress API get response status: {response.status_code}")
            
            # For error responses, log the response content
            if response.status_code >= 400:
                self.logger.error(f"WordPress API get error response: {response.text}")
            
            # Check if request was successful
            response.raise_for_status()
            
            # Parse response
            response_data = response.json()
            
            self.logger.info(f"Article retrieved successfully from WordPress")
            
            return {
                'success': True,
                'article': response_data
            }
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get article from WordPress: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_or_create_tags(self, tag_names):
        """
        Get or create tags in WordPress and return their IDs.
        
        Args:
            tag_names: List of tag names
            
        Returns:
            list: List of tag IDs
        """
        tag_ids = []
        
        for tag_name in tag_names:
            # First check if the tag exists
            try:
                self.logger.info(f"Checking if tag '{tag_name}' exists in WordPress")
                
                # URL encode the tag name for the search
                import urllib.parse
                encoded_tag = urllib.parse.quote(tag_name)
                
                response = requests.get(
                    f"{self.api_url}/tags",
                    params={"search": encoded_tag},
                    auth=(self.username, self.password)
                )
                
                response.raise_for_status()
                existing_tags = response.json()
                
                # Check if we found an exact match
                tag_id = None
                for tag in existing_tags:
                    if tag.get('name', '').lower() == tag_name.lower():
                        tag_id = tag['id']
                        self.logger.info(f"Found existing tag '{tag_name}' with ID: {tag_id}")
                        break
                
                # If tag doesn't exist, create it
                if not tag_id:
                    self.logger.info(f"Tag '{tag_name}' not found, creating it")
                    
                    create_response = requests.post(
                        f"{self.api_url}/tags",
                        json={"name": tag_name},
                        auth=(self.username, self.password),
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    create_response.raise_for_status()
                    tag_data = create_response.json()
                    tag_id = tag_data.get('id')
                    
                    self.logger.info(f"Created tag '{tag_name}' with ID: {tag_id}")
                
                if tag_id:
                    tag_ids.append(tag_id)
                
            except Exception as e:
                self.logger.error(f"Error handling tag '{tag_name}': {str(e)}")
        
        self.logger.info(f"Final tag IDs: {tag_ids}")
        return tag_ids