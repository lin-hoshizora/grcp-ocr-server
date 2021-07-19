"""Analyzer that extracts key information from OCR resutls of 主保険"""
from typing import List, Any
import regex as re
import numpy as np
from .finders import RouFtnKbnFinder, KigoNumFinder
from .analyzer_base import AnalyzerBase
from .extract import get_insurer_num, get_num, get_date
from .match import skkget_match


def preprocess(texts: List[List[Any]]):
  """Fixes some common issues in OCR results.

  Args:
    texts: OCR results in a list.
  """
  for idx, line in enumerate(texts):
    texts[idx][-1] = line[-1].replace("令和年", "令和元年")

  # remove repeating 1
  for idx, line in enumerate(texts):
    if "保険者番号" not in line[-1] or "11" not in line[-1]:
      continue
    pos = line[-1].index("11")
    probs = np.hstack([w[1] for w in line[:-1]])
    if (min(probs[pos], probs[pos + 1]) < 0.7 and
        max(probs[pos], probs[pos + 1]) > 0.9):
      texts[idx][-1] = line[-1][:pos + 1] + line[-1][pos + 2:]

  # add undetected hyphen
  for idx, line in enumerate(texts):
    if "記号" not in line[-1]:
      continue
    for w_idx, w1 in enumerate(line[:-2]):
      w2 = line[w_idx + 1]
      if (len(w1[0]) > 1 and len(w2[0]) > 1 and
          w1[0].isdigit() and w2[0].isdigit()):
        w1_right = w1[3][0] + w1[2][-1]
        w2_left = w2[3][0] + w2[2][0]
        gap_avg1 = (w1[2][1:] - w1[2][:-1]).mean()
        gap_avg2 = (w2[2][1:] - w2[2][:-1]).mean()
        gap_avg = (gap_avg1 + gap_avg2) / 2
        if w2_left - w1_right > gap_avg * 3:
          start = sum(len(w[0]) for w in line[:w_idx + 1])
          texts[idx][-1] = line[-1][:start] + "-" + line[-1][start:]

  for idx, line in enumerate(texts):
    if ("番号" not in line[-1][:-4]):
      continue
    if not line[-1][-2:].isdigit():
      continue

    # add "枝番" for easier extraction if 番号 in the line, and the last box
    # has only 2 digits
    if (len(line) > 2 and len(line[-2][0]) == 2):
      texts[idx][-1] = line[-1][:-2] + "枝番" + line[-1][-2:]
      continue

    # add "枝番" for easier extraction if the last 2 chars in the last box
    # are digits and far away from other chars
    if len(line[-2][0]) >= 4:
      positions = line[-2][2]
      pos_others = line[-2][2][:-2]
      inter_other_avg = pos_others[1:] - pos_others[:-1]
      space = positions[-2] - positions[-3]
      if space > inter_other_avg.mean() * 2:
        texts[idx][-1] = line[-1][:-2] + "枝番" + line[-1][-2:]

  return texts


class KoureiAnalyzer(AnalyzerBase):
  """Analyzer to extract key information from OCR results of 主保険.

  It tries to extract as much keyinformation as possible when `fit` is called.
  The input argument `texts` of `fit` is a list containing OCR results, each
  element of which also has to be a list, whose last element has to be text of
  one line.

  All extracted information is stored in info, and can be queried by tag via
  `get`.

  Typical usage example:
    >>> analyzer = MainAnalyzer()
    >>> analyzer.fit([["a str", "保険者番号12345678"], [["a list"], "記号1番号2"]])
    >>> print(analyzer.get("HknajaNum"))
    12345678
    >>> print(analyzer.get("Kigo"))
    1
    >>> print(analyzer.get("Num"))
    2

  To add a new item as extraction target:
    Add a finder in `config`. All finders in `config` will be called, and all
    extracted information will be stored in `info`

  To add fallback processing to catch patterns that cannot be handled by finders
  in `config`:
    It is recommended to add a new internal method can call it in `fit`. Check
    `_handle_branch`, `_handle_hknjanum`, `_trim_hknjanum`, `_clean_kigo_num`
    for examples.
  """
  def __init__(self):
    config = {
        ("Birthday", "YukoStYmd", "YukoEdYmd", "KofuYmd"): "dates_finder",
        "RouFtnKbn": RouFtnKbnFinder(),
    }
    super().__init__(config)

  def fit(self, texts: List[List[Any]]):
    """Extracts key information from OCR results.

    Args:
      texts: OCR results in a list.
    """
    texts = preprocess(texts)
    self._finder_fit(texts)
  