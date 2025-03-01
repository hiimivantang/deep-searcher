import logging
import time
from termcolor import colored

class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': 'cyan',      
        'INFO': 'green',      
        'WARNING': 'yellow',  
        'ERROR': 'red',       
        'CRITICAL': 'magenta'
    }

    def format(self, record):
        # all line in log will be colored
        log_message = super().format(record)
        return colored(log_message, self.COLORS.get(record.levelname, 'white'))

        # only log level will be colored
        # levelname_colored = colored(record.levelname, self.COLORS.get(record.levelname, 'white'))
        # record.levelname = levelname_colored 
        # return super().format(record)
        
        # only keywords will be colored
        # message = record.msg
        # for word, color in self.KEYWORDS.items():
        #     if word in message:
        #         message = message.replace(word, colored(word, color))
        # record.msg = message
        # return super().format(record)

# config log
dev_logger = logging.getLogger("dev")
dev_formatter = ColoredFormatter("%(asctime)s - %(levelname)s - %(message)s")
dev_handler = logging.StreamHandler()
dev_handler.setFormatter(dev_formatter)
dev_logger.addHandler(dev_handler)
dev_logger.setLevel(logging.INFO)

progress_logger= logging.getLogger("progress")
progress_handler = logging.StreamHandler()
progress_handler.setFormatter(ColoredFormatter("%(message)s"))
progress_logger.addHandler(progress_handler)
progress_logger.setLevel(logging.INFO)

dev_mode = False

def set_dev_mode(mode: bool):
    """set dev mode"""
    global dev_mode
    dev_mode = mode

def set_level(level):
    """set log level"""
    dev_logger.setLevel(level)


def debug(message):
    """debug log"""
    if dev_mode:
        dev_logger.debug(message)


def info(message):
    """info log"""
    if dev_mode:
        dev_logger.info(message)


def warning(message):
    """warning log"""
    if dev_mode:
        dev_logger.warning(message)


def error(message):
    """error log"""
    if dev_mode:
        dev_logger.error(message)


def critical(message):
    """critical log"""
    if dev_mode:
        dev_logger.critical(message)

def color_print(message, same_line=False, task_id="default", progress_type=None, **kwargs):
    """Print a colored message, optionally on the same line, and track progress
    
    Args:
        message: The message to print
        same_line: If True, print on the same line, otherwise print a new line
        task_id: An identifier for the task this progress message belongs to
        progress_type: Type of progress (loading, embedding, chunking, etc.)
    """
    # Determine message type based on content
    if progress_type is None:
        if "🔄" in message:
            progress_type = "initializing"
        elif "📚" in message:
            progress_type = "loading"
        elif "✂️" in message:
            progress_type = "chunking"
        elif "🔢" in message:
            progress_type = "embedding"
        elif "💾" in message:
            progress_type = "storing"
        elif "🎉" in message:
            progress_type = "complete"
        else:
            progress_type = "info"
    
    if same_line:
        inline_progress(message, same_line=True, task_id=task_id, progress_type=progress_type)
    else:
        progress_logger.info(message)
        
        # Also update progress tracking for non-inline messages
        # Extract percentage if available
        percentage = 0
        if "%" in message:
            try:
                percentage_part = message.split("%")[0].split(" ")[-1].strip()
                percentage = float(percentage_part)
            except Exception:
                percentage = 0
                
        # Update progress status
        _current_progress[task_id] = {
            "message": message,
            "type": progress_type,
            "percentage": percentage,
            "timestamp": time.time()
        }
        
        # Notify subscribers
        for callback in _progress_callbacks:
            try:
                callback(_current_progress)
            except Exception as e:
                print(f"Error in progress callback: {e}")
    
def inline_progress(message, same_line=True, task_id="default", progress_type="loading"):
    """Print progress updates that overwrite the previous line and notify subscribers
    
    Args:
        message: The progress message to display
        same_line: Whether to overwrite the previous line (True) or print a new line (False)
        task_id: An identifier for the task this progress message belongs to
        progress_type: Type of progress (loading, embedding, chunking, etc.)
    """
    if same_line:
        # Use carriage return to update progress on the same line
        print(f"\r{message}", end="", flush=True)
    else:
        # End the current line and start a new one
        print(f"\r{message}")
    
    # Extract percentage if available
    percentage = 0
    if "%" in message:
        try:
            # Try to extract percentage from strings like "70.5%"
            percentage_part = message.split("%")[0].split(" ")[-1].strip()
            percentage = float(percentage_part)
        except Exception:
            percentage = 0
    
    # Update progress status
    _current_progress[task_id] = {
        "message": message,
        "type": progress_type,
        "percentage": percentage,
        "timestamp": time.time()
    }
    
    # Notify subscribers
    for callback in _progress_callbacks:
        try:
            callback(_current_progress)
        except Exception as e:
            print(f"Error in progress callback: {e}")
        
# Dictionary to track current progress by task id
_current_progress = {}
_progress_callbacks = []

def register_progress_callback(callback):
    """Register a callback function to be called when progress is updated
    
    Args:
        callback: A function that takes a progress message and status
    """
    if callback not in _progress_callbacks:
        _progress_callbacks.append(callback)
        
def unregister_progress_callback(callback):
    """Unregister a progress callback function
    
    Args:
        callback: The callback function to remove
    """
    if callback in _progress_callbacks:
        _progress_callbacks.remove(callback)
        
def get_progress_status():
    """Get the current progress status
    
    Returns:
        dict: A dictionary with the current status of all tasks
    """
    return dict(_current_progress)