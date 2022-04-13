"""
`fbref` data collection.
"""

__author__ = 'Abner Rios'
__version__ = '0.0.1'
__license__ = 'MIT'

from .element import ScheduledMatches

class FbrefDayMatches(ScheduledMatches):
  def __init__(self) -> None:
      super().__init__()