import re
from typing import Dict, Any, Optional
from crewai.tools import BaseTool

class CommandParserTool(BaseTool):
    """
    Tool for parsing natural language commands into structured editing actions.
    """

    name: str = "command_parser"
    description: str = "Parses natural language commands into structured editing actions with action type, target, position, and content."

    def _run(self, command: str) -> Dict[str, Any]:
        """
        Parse a natural language command into structured editing action.

        Args:
            command: The natural language command to parse

        Returns:
            Dict containing parsed action details
        """
        command = command.lower().strip()

        # Define action patterns
        action_patterns = {
            'add': r'\b(add|insert|include|put)\b',
            'remove': r'\b(remove|delete|eliminate|cut)\b',
            'modify': r'\b(change|modify|update|replace|make|rewrite)\b',
            'replace': r'\b(replace|swap|switch)\b'
        }

        # Define target patterns
        target_patterns = {
            'title': r'\b(title|headline)\b',
            'content': r'\b(content|body|text|article)\b',
            'introduction': r'\b(intro|introduction|beginning|start)\b',
            'conclusion': r'\b(conclusion|ending|end|summary)\b',
            'paragraph': r'\b(paragraph|section)\b',
            'image': r'\b(image|picture|photo|graphic)\b',
            'heading': r'\b(heading|header|h[1-6])\b'
        }

        # Define position patterns
        position_patterns = {
            'before': r'\b(before|prior to|in front of)\b',
            'after': r'\b(after|following|behind)\b',
            'first': r'\b(first|initial|opening)\b',
            'last': r'\b(last|final|closing)\b',
            'beginning': r'\b(beginning|start|top)\b',
            'end': r'\b(end|bottom)\b'
        }

        # Extract action
        action = None
        for action_type, pattern in action_patterns.items():
            if re.search(pattern, command):
                action = action_type
                break

        # Extract target
        target = None
        for target_type, pattern in target_patterns.items():
            if re.search(pattern, command):
                target = target_type
                break

        # Extract position
        position = None
        for position_type, pattern in position_patterns.items():
            if re.search(pattern, command):
                position = position_type
                break

        # Extract specific numbers (like "second paragraph")
        number_match = re.search(r'\b(\d+)(?:st|nd|rd|th)?\b', command)
        if number_match:
            position = f"{number_match.group(1)}"

        # Extract content (everything after common separators)
        content_separators = [r'to\s+', r'with\s+', r':\s*', r'-\s*']
        content = None
        for separator in content_separators:
            match = re.search(separator + r'(.*)', command, re.IGNORECASE)
            if match:
                content = match.group(1).strip()
                break

        # If no content found, try to extract quoted text
        if not content:
            quotes = re.findall(r'"([^"]*)"', command)
            if quotes:
                content = quotes[0]

        # Handle special cases
        if not action and 'make' in command and 'more' in command:
            action = 'modify'
            if 'engaging' in command or 'interesting' in command:
                content = 'more engaging'

        if target == 'paragraph' and position and position.isdigit():
            target = f'paragraph_{position}'

        result = {
            'action': action,
            'target': target,
            'position': position,
            'content': content,
            'confidence': self._calculate_confidence(action, target, position, content),
            'original_command': command
        }

        return result

    def _calculate_confidence(self, action: Optional[str], target: Optional[str],
                            position: Optional[str], content: Optional[str]) -> float:
        """
        Calculate confidence score for the parsing result.
        """
        confidence = 0.0

        if action:
            confidence += 0.3
        if target:
            confidence += 0.3
        if position:
            confidence += 0.2
        if content:
            confidence += 0.2

        return min(confidence, 1.0)