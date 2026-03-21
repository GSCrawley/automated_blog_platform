from typing import Dict, Any, Optional
import re
from crewai.tools import BaseTool

class ContentModifierTool(BaseTool):
    """
    Tool for applying modifications to article content.
    """

    name: str = "content_modifier"
    description: str = "Applies text-based modifications to article content including additions, removals, and replacements."

    def _run(self, article_content: str, action: str, target: str,
             position: Optional[str] = None, content: Optional[str] = None) -> Dict[str, Any]:
        """
        Apply a modification to article content.

        Args:
            article_content: The original article content
            action: The action to perform (add, remove, modify, replace)
            target: The target element (title, content, paragraph, etc.)
            position: Where to apply the change
            content: The new content to add/modify

        Returns:
            Dict containing the modified content and change details
        """
        original_content = article_content

        if action == 'add':
            modified_content = self._add_content(article_content, target, position, content)
        elif action == 'remove':
            modified_content = self._remove_content(article_content, target, position)
        elif action == 'modify':
            modified_content = self._modify_content(article_content, target, position, content)
        elif action == 'replace':
            modified_content = self._replace_content(article_content, target, position, content)
        else:
            return {
                'success': False,
                'error': f'Unsupported action: {action}',
                'original_content': original_content
            }

        # Calculate diff for change tracking
        changes = self._calculate_changes(original_content, modified_content)

        return {
            'success': True,
            'modified_content': modified_content,
            'changes': changes,
            'action_performed': action,
            'target': target,
            'position': position
        }

    def _add_content(self, content: str, target: str, position: Optional[str],
                    new_content: Optional[str]) -> str:
        """
        Add content to the article.
        """
        if not new_content:
            return content

        if target == 'title':
            # For title modifications, we'd need to handle this at the article level
            # For now, return unchanged
            return content

        elif target in ['content', 'introduction', 'conclusion']:
            return self._add_to_section(content, target, position, new_content)

        elif target.startswith('paragraph_'):
            return self._add_to_paragraph(content, target, position, new_content)

        # Default: append to end
        return content + '\n\n' + new_content

    def _remove_content(self, content: str, target: str, position: Optional[str]) -> str:
        """
        Remove content from the article.
        """
        if target.startswith('paragraph_'):
            return self._remove_paragraph(content, target)

        # For other targets, we'd need more specific logic
        return content

    def _modify_content(self, content: str, target: str, position: Optional[str],
                       new_content: Optional[str]) -> str:
        """
        Modify existing content.
        """
        if target == 'title':
            # Handle title changes at article level
            return content

        # For general content modifications
        if position and new_content:
            # This is a simplified implementation
            # In practice, you'd want more sophisticated content modification logic
            return content.replace(position, new_content) if position in content else content

        return content

    def _replace_content(self, content: str, target: str, position: Optional[str],
                        new_content: Optional[str]) -> str:
        """
        Replace content in the article.
        """
        return self._modify_content(content, target, position, new_content)

    def _add_to_section(self, content: str, section: str, position: str,
                       new_content: str) -> str:
        """
        Add content to a specific section.
        """
        paragraphs = content.split('\n\n')
        section_keywords = {
            'introduction': ['introduction', 'intro', 'overview', 'background'],
            'conclusion': ['conclusion', 'summary', 'final thoughts', 'in conclusion']
        }

        if section in section_keywords:
            keywords = section_keywords[section]
            for i, para in enumerate(paragraphs):
                if any(keyword in para.lower() for keyword in keywords):
                    if position == 'after':
                        paragraphs.insert(i + 1, new_content)
                    elif position == 'before':
                        paragraphs.insert(i, new_content)
                    break

        return '\n\n'.join(paragraphs)

    def _add_to_paragraph(self, content: str, target: str, position: str,
                         new_content: str) -> str:
        """
        Add content to a specific paragraph.
        """
        try:
            para_index = int(target.split('_')[1])
            paragraphs = content.split('\n\n')

            if 0 <= para_index < len(paragraphs):
                if position == 'after':
                    paragraphs.insert(para_index + 1, new_content)
                elif position == 'before':
                    paragraphs.insert(para_index, new_content)
                elif position == 'end':
                    paragraphs[para_index] += ' ' + new_content
                elif position == 'beginning':
                    paragraphs[para_index] = new_content + ' ' + paragraphs[para_index]

            return '\n\n'.join(paragraphs)
        except (ValueError, IndexError):
            return content

    def _remove_paragraph(self, content: str, target: str) -> str:
        """
        Remove a specific paragraph.
        """
        try:
            para_index = int(target.split('_')[1])
            paragraphs = content.split('\n\n')

            if 0 <= para_index < len(paragraphs):
                paragraphs.pop(para_index)

            return '\n\n'.join(paragraphs)
        except (ValueError, IndexError):
            return content

    def _calculate_changes(self, original: str, modified: str) -> Dict[str, Any]:
        """
        Calculate the differences between original and modified content.
        """
        original_lines = original.split('\n')
        modified_lines = modified.split('\n')

        return {
            'lines_added': len(modified_lines) - len(original_lines),
            'lines_removed': len(original_lines) - len(modified_lines),
            'characters_added': len(modified) - len(original),
            'characters_removed': len(original) - len(modified),
            'word_count_change': len(modified.split()) - len(original.split())
        }