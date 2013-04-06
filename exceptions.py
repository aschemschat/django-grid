"""
This file contains all exceptions, the grid may be throwing 
"""

class GridException(Exception):
    """
    Baseexception for all grid-related exceptions
    """
    def __init__(self, msg=None, exception=None):
        super(GridException, self).__init__(msg)
        self.exception = exception

class GridConfigurationException(GridException):
    """ Exception thrown, if something during the initialization/configuration of the grid 
    went wrong. """
    pass
