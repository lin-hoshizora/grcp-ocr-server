"""A naive key information finder"""
import yaml
from .. import match as m
from .. import extract as e


class SimpleFinder(yaml.YAMLObject):
  """A naive key information finder.

  It matches a pattern in each given line, and extracts information from the
  exact line where the pattern is successfully matched.

  YAMLObject: This class can be saved as a YAML file for reuse.

  Typical usage example:
    >>> finder = SimpleFinder(
          match_method="birthday_match",
          extract_method="get_date"
        )
    >>> print(finder.extract([["生年月日1960年12月12日"], ["another line"]]))
    [19601212]

  Args:
    match_method: Name of the function for pattern matching, which has to be
        defined in `..match`
    extract_method: Name of the function for information extraction, which has
        to be defined in `..extract`
  """
  yaml_tag = u'!SimpleFinder'
  def __init__(self, match_method: str, extract_method: str):
    self.mf = getattr(m, match_method)
    self.ef = getattr(e, extract_method)

  def match_one(self, texts):
    for line in texts:
      ret, text = self.mf(line[-1])
      if ret:
        return text
    return None

  def extract(self, texts):
    text = self.match_one(texts)
    if text is not None:
      res = self.ef(text)
      return res
    return None
