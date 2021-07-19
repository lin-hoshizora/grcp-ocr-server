"""
Abstract Class for Scanner
"""


class Scanner:
  """
  An abstract class
  """
  def __init__(self):
    """
    Init Process
    """
    raise NotImplementedError

  def scan(self):
    """
    Start scan
    :return: scanned image
    """
    raise NotImplementedError

  def reconnect(self):
    """
    Reconnect the scanner
    :return:
    """
    raise NotImplementedError

  def __str__(self):
    """
    Debug Info
    :return: print out debug info to screen
    """
    raise NotImplementedError
