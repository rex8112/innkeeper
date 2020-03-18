class Error(Exception):
    """Base Class for Adventure exceptions"""
    pass

class InvalidLevel(Error):
    """Raised when level does not meet the criteria for a task"""
    pass

class InvalidRequirements(Error):
    """Raised when an adventurer does not meet necessary requirements"""
    pass

class AdventurerBusy(Error):
    """Raised when an adventurer can not complete a task because he is busy"""
    pass