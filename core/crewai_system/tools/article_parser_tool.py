import re
from typing import Dict, List, Any
from crewai.tools import BaseTool

class ArticleParserTool(BaseTool):
    """
    Tool for parsing and analyzing article content structure.
    """

    name: str = "article_parser"
    description: str = "Parses article content into structured sections, paragraphs, and elements for targeted editing."

    def _run(self, article_content: str) -> Dict[str, Any]:
        """
        Parse article content into structured components.

        Args:
            article_content: The full article content to parse

        Returns:
            Dict containing parsed article structure
        """
        # Split into paragraphs
        paragraphs = self._split_into_paragraphs(article_content)

        # Identify sections and headings
        sections = self._identify_sections(article_content)

        # Extract metadata
        metadata = self._extract_metadata(article_content)

        # Find images and media
        media_elements = self._find_media_elements(article_content)

        return {
            'paragraphs': paragraphs,
            'sections': sections,
            'metadata': metadata,
            'media_elements': media_elements,
            'total_paragraphs': len(paragraphs),
            'total_sections': len(sections),
            'word_count': len(article_content.split()),
            'character_count': len(article_content)
        }

    def _split_into_paragraphs(self, content: str) -> List[Dict[str, Any]]:
        """
        Split content into paragraphs with metadata.
        """
        # Split by double newlines or paragraph markers
        raw_paragraphs = re.split(r'\n\s*\n', content.strip())

        paragraphs = []
        current_position = 0

        for i, para in enumerate(raw_paragraphs):
            para = para.strip()
            if not para:
                continue

            # Calculate position info
            start_pos = content.find(para, current_position)
            end_pos = start_pos + len(para)

            paragraphs.append({
                'index': i,
                'content': para,
                'word_count': len(para.split()),
                'start_position': start_pos,
                'end_position': end_pos,
                'is_heading': self._is_heading(para),
                'heading_level': self._get_heading_level(para) if self._is_heading(para) else None
            })

            current_position = end_pos

        return paragraphs

    def _identify_sections(self, content: str) -> List[Dict[str, Any]]:
        """
        Identify sections and their content.
        """
        sections = []
        lines = content.split('\n')

        current_section = None
        current_content = []

        for line in lines:
            line = line.strip()
            if self._is_heading(line):
                # Save previous section
                if current_section:
                    sections.append({
                        'heading': current_section,
                        'content': '\n'.join(current_content).strip(),
                        'heading_level': self._get_heading_level(current_section)
                    })

                # Start new section
                current_section = line
                current_content = []
            else:
                if current_section:
                    current_content.append(line)

        # Add final section
        if current_section:
            sections.append({
                'heading': current_section,
                'content': '\n'.join(current_content).strip(),
                'heading_level': self._get_heading_level(current_section)
            })

        return sections

    def _extract_metadata(self, content: str) -> Dict[str, Any]:
        """
        Extract metadata from content.
        """
        return {
            'has_introduction': self._has_introduction(content),
            'has_conclusion': self._has_conclusion(content),
            'has_images': '<img' in content.lower() or '![' in content,
            'has_links': '[' in content and '](' in content,
            'has_lists': any(marker in content for marker in ['- ', '* ', '1. ', '2. ']),
            'estimated_reading_time': max(1, len(content.split()) // 200)  # ~200 words per minute
        }

    def _find_media_elements(self, content: str) -> List[Dict[str, Any]]:
        """
        Find images and other media elements in content.
        """
        media_elements = []

        # Find markdown images
        markdown_images = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', content)
        for alt_text, url in markdown_images:
            media_elements.append({
                'type': 'image',
                'format': 'markdown',
                'alt_text': alt_text,
                'url': url,
                'position': content.find(f'![{alt_text}]({url})')
            })

        # Find HTML images
        html_images = re.findall(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>', content, re.IGNORECASE)
        for url in html_images:
            media_elements.append({
                'type': 'image',
                'format': 'html',
                'url': url,
                'position': content.find(url)
            })

        return media_elements

    def _is_heading(self, text: str) -> bool:
        """
        Check if text is a heading.
        """
        return bool(re.match(r'^#{1,6}\s+', text) or  # Markdown headings
                   re.match(r'^<h[1-6]', text.lower()))  # HTML headings

    def _get_heading_level(self, text: str) -> int:
        """
        Get heading level (1-6).
        """
        # Markdown headings
        markdown_match = re.match(r'^(#{1,6})', text)
        if markdown_match:
            return len(markdown_match.group(1))

        # HTML headings
        html_match = re.search(r'<h([1-6])', text.lower())
        if html_match:
            return int(html_match.group(1))

        return 1

    def _has_introduction(self, content: str) -> bool:
        """
        Check if content has an introduction section.
        """
        intro_keywords = ['introduction', 'intro', 'overview', 'background', 'beginning']
        first_200_words = ' '.join(content.split()[:200]).lower()
        return any(keyword in first_200_words for keyword in intro_keywords)

    def _has_conclusion(self, content: str) -> bool:
        """
        Check if content has a conclusion section.
        """
        conclusion_keywords = ['conclusion', 'summary', 'final thoughts', 'in conclusion', 'wrapping up']
        last_200_words = ' '.join(content.split()[-200:]).lower()
        return any(keyword in last_200_words for keyword in conclusion_keywords)