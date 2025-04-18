import re
from typing import List, Optional, Tuple, Union


class FrameRange:
    """
    Class for validating and processing frame range strings with token substitution.
    
    Supports syntax like:
    - 1-10 (simple range)
    - 1,3,9 (comma separated list)
    - 1-90x3 or 1-90/3 (stepped range with x or / syntax)
    - 9,50,100-200 (mixed comma list and range)
    - 9-18x2,100 (mixed stepped range and single frames)
    
    Tokens that can be substituted:
    - f = first_frame
    - m = middle_frame (the average of first and last frame)
    - l = last_frame
    - hero = hero_frames (comma separated list of frames)
    
    Usage:
        # Create a frame range object
        fr = FrameRange("1-10,20,30-40x2")
        
        # Validate syntax
        if fr.is_valid_syntax():
            # Get expanded list of frames
            frames = fr.expand_range()
        
        # With token substitution from Nuke
        fr = FrameRange("f-l")
        fr.substitute_tokens_from_nuke()
        frames = fr.expand_range()
        
        # With token substitution from a Nuke script file
        fr = FrameRange("f,hero")
        with open("my_script.nk", "r") as f:
            script_content = f.read()
        fr.substitute_tokens_from_script(script_content)
        frames = fr.expand_range()
    """
    
    # Regular expressions for validation
    RANGE_PATTERN = r'(\d+|\w+)-(\d+|\w+)(?:x(\d+)|/(\d+))?'
    SINGLE_PATTERN = r'(\d+|\w+)'
    FRAME_RANGE_PATTERN = fr'^({RANGE_PATTERN}|{SINGLE_PATTERN})(?:,({RANGE_PATTERN}|{SINGLE_PATTERN}))*$'
    
    # Token patterns
    TOKEN_PATTERN = r'(f|m|l|hero)\b'
    
    def __init__(self, frame_range_str: str = ""):
        """
        Initialize with a frame range string.
        
        Args:
            frame_range_str: A string representing a frame range
        """
        self.original_str = frame_range_str
        self.processed_str = ""
        self.has_tokens = bool(re.search(self.TOKEN_PATTERN, frame_range_str))
    
    def is_valid_syntax(self) -> bool:
        """
        Check if the frame range string has valid syntax.
        
        Returns:
            bool: True if syntax is valid, False otherwise
        """
        if not self.original_str:
            return False
        
        return bool(re.match(self.FRAME_RANGE_PATTERN, self.original_str))
    
    @staticmethod
    def normalize_hero_frames(hero_frames: str) -> str:
        """
        Normalize hero frames string to comma-separated format without extra spaces.
        Handles various delimiters (commas, spaces, or mixed).
        
        Args:
            hero_frames: Hero frames string in any format
            
        Returns:
            str: Normalized comma-separated hero frames
        """
        if not hero_frames:
            return ""
            
        # Replace any combination of spaces and commas with a single space
        normalized = re.sub(r'[,\s]+', ' ', hero_frames.strip())
        
        # Split by space and rejoin with commas
        frame_list = normalized.split()
        return ','.join(frame_list)
    
    def substitute_tokens(self, first_frame: Optional[Union[int, float]] = None, 
                         last_frame: Optional[Union[int, float]] = None,
                         hero_frames: Optional[str] = None) -> str:
        """
        Substitute tokens in the frame range string with actual values.
        Only performs substitution if tokens are present.
        
        Args:
            first_frame: Value to substitute for 'f' token
            last_frame: Value to substitute for 'l' token
            hero_frames: Value to substitute for 'hero' token
            
        Returns:
            str: Frame range string with tokens substituted
        """
        if not self.has_tokens:
            self.processed_str = self.original_str
            return self.processed_str
        
        # Make a copy of the original string for processing
        result = self.original_str
        
        # Calculate middle frame if first and last frames are provided
        middle_frame = None
        if first_frame is not None and last_frame is not None:
            middle_frame = int((first_frame + last_frame) / 2)
        
        # Substitute tokens
        if first_frame is not None:
            result = re.sub(r'\bf\b', str(int(first_frame)), result)
        
        if middle_frame is not None:
            result = re.sub(r'\bm\b', str(middle_frame), result)
            
        if last_frame is not None:
            result = re.sub(r'\bl\b', str(int(last_frame)), result)
            
        if hero_frames is not None:
            normalized_hero_frames = self.normalize_hero_frames(hero_frames)
            result = re.sub(r'\bhero\b', normalized_hero_frames, result)
            
        self.processed_str = result
        return result
    
    def substitute_tokens_from_nuke(self) -> str:
        """
        Substitute tokens using values from Nuke environment.
        Only performs substitution if tokens are present.
        
        Returns:
            str: Frame range string with tokens substituted
        
        Raises:
            ImportError: If not running in a Nuke environment
        """
        if not self.has_tokens:
            self.processed_str = self.original_str
            return self.processed_str
        
        try:
            import nuke
            root = nuke.root()
            first_frame = int(root['first_frame'].value())
            last_frame = int(root['last_frame'].value())
            
            # Try to get hero frames from custom knob
            hero_frames = None
            if 'heroFrames' in root.knobs():
                hero_frames = root['heroFrames'].value()
            
            return self.substitute_tokens(first_frame, last_frame, hero_frames)
        except ImportError:
            # Not in Nuke environment
            self.processed_str = self.original_str
            return self.processed_str
    
    def substitute_tokens_from_script(self, script_content: str) -> str:
        """
        Substitute tokens using values extracted from a Nuke script file content.
        Only performs substitution if tokens are present.
        
        Args:
            script_content: Content of the Nuke script file
            
        Returns:
            str: Frame range string with tokens substituted
        """
        if not self.has_tokens:
            self.processed_str = self.original_str
            return self.processed_str
        
        # Extract frame information from the script
        first_frame_match = re.search(r'first_frame\s+(\d+)', script_content)
        last_frame_match = re.search(r'last_frame\s+(\d+)', script_content)
        hero_frames_match = re.search(r'heroFrames\s+(.+?)(?:\n|$)', script_content)
        
        first_frame = int(first_frame_match.group(1)) if first_frame_match else None
        last_frame = int(last_frame_match.group(1)) if last_frame_match else None
        hero_frames = hero_frames_match.group(1).strip() if hero_frames_match else None
        
        return self.substitute_tokens(first_frame, last_frame, hero_frames)
    
    def expand_range(self) -> List[int]:
        """
        Expand the processed frame range string into a list of frame numbers.
        
        Returns:
            List[int]: List of frame numbers specified by the range
            
        Raises:
            ValueError: If the frame range syntax is invalid or token substitution is needed
        """
        if not self.processed_str:
            if self.has_tokens:
                raise ValueError("Token substitution needed before expanding range")
            self.processed_str = self.original_str
            
        if not self.is_valid_syntax():
            raise ValueError(f"Invalid frame range syntax: {self.processed_str}")
            
        result = []
        parts = self.processed_str.split(',')
        
        for part in parts:
            if '-' in part:
                range_parts = re.match(r'(\d+)-(\d+)(?:x(\d+)|/(\d+))?', part)
                if range_parts:
                    try:
                        start = int(range_parts.group(1))
                        end = int(range_parts.group(2))
                        step = int(range_parts.group(3) or range_parts.group(4) or 1)
                        
                        if step <= 0:
                            raise ValueError(f"Step value must be positive in range: {part}")
                        
                        if start > end:
                            raise ValueError(f"Start frame must be less than or equal to end frame in range: {part}")
                            
                        result.extend(range(start, end + 1, step))
                    except (ValueError, TypeError) as e:
                        raise ValueError(f"Error parsing range '{part}': {str(e)}")
                else:
                    raise ValueError(f"Invalid range format: {part}")
            else:
                try:
                    result.append(int(part))
                except ValueError:
                    raise ValueError(f"Invalid frame number: {part}")
                
        return sorted(result)
    
    def __str__(self) -> str:
        """String representation of the frame range."""
        return self.processed_str if self.processed_str else self.original_str
