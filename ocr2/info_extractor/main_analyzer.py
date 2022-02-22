"""Analyzer that extracts key information from OCR resutls of 主保険"""
from pydoc import text
from typing import List, Any
from unicodedata import name
import regex as re
import numpy as np
from .finders import RouFtnKbnFinder, KigoNumFinder
from .analyzer_base import AnalyzerBase
from .extract import get_insurer_num, get_num, get_date
from .match import skkget_match
from .HknjaNum_list import HknjaNum_LIST,HonKKEY,HonKKEY_FINDER,HknjaNum_no_1_LIST 


def preprocess(texts: List[List[Any]]):
  """Fixes some common issues in OCR results.

  Args:
    texts: OCR results in a list.
  """
  for idx, line in enumerate(texts):
    reiwa = re.compile(r'(令?和|令和?)')
    texts[idx][-1] = line[-1].replace("令和年", "令和元年")
    texts[idx][-1] = reiwa.sub('令和',line[-1])

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
    # print(56,len(line),line[-2][0])
    if (len(line) > 2 and len(line[-2][0]) == 2):
      texts[idx][-1] = line[-1][:-2] + "枝番" + line[-1][-2:]
      continue

    # add "枝番" for easier extraction if the last 2 chars in the last box
    # are digits and far away from other chars
    try:
      if len(line[-2][0]) >= 4:
        positions = line[-2][2]
        pos_others = line[-2][2][:-2]
        inter_other_avg = pos_others[1:] - pos_others[:-1]
        space = positions[-2] - positions[-3]
        #2 -> 3
        if space > inter_other_avg.mean() * 3:
          texts[idx][-1] = line[-1][:-2] + "枝番" + line[-1][-2:]
    except:
      print('branch number preprocess')

  return texts


class MainAnalyzer(AnalyzerBase):
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
        "HknjaNum": "wide_finder",
        ("Kigo", "Num"): KigoNumFinder(),
        ("Birthday", "YukoStYmd", "YukoEdYmd", "KofuYmd"): "dates_finder",
        "Branch": "wide_finder",
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
    self._handle_hknjanum(texts)
    self._trim_hknjanum(texts)
    self._handle_branch(texts)
    self._handle_kigo_num(texts)
    self._get_SkkGetYmd(texts)
    self._get_HonKzkKbn(texts)
    self._clean_kigo_num()
    self._check_HKB_with_list(texts)
    self._check_Kigo_with_nashi()
    self._check_SkkGetYmd_and_Num_with_hknjanum_(texts)
    self._check_HKB_with_no_1_list(texts)
    self._except_YukoEdYmd(texts)
    self._check_oneLine_have_YukoEdYmd_YukoStYmd_(texts)


  def _handle_branch(self, texts: List[List[Any]]):
    """Fallback handling when the corresponding finder cannnot extract Branch.

    Args:
      texts: OCR results in a list.
    """
    # handle 番号 123 番123
    # print(1)
    if self._have("Branch"): return
    for line in texts:
      if "番号" not in line[-1]: continue
      res = re.findall(r"番号\d+\(?番\)?(\d+)", line[-1])
      # print(res, line[-1])
      if res and res[0]:
        self.info["Branch"] = res[0]
        break

  def _handle_kigo_num(self, texts: List[List[Any]]):
    """Fallback handling when Kigo, Num are seperated by another line

    Args:
      texts: OCR results in a list.
    """
    if (self.info.get("Kigo", None) is not None or
        self.info.get("Num", None) is not None):
      return

    for idx, line in enumerate(texts[:-2]):
      if "記号" in line[-1] and "番号" in texts[idx + 2][-1]:
        self.info["Kigo"] = line[-1][(line[-1].index("記号") + 2):]
        self.info["Num"] = get_num(texts[idx + 2][-1])
        break

  def _clean_kigo_num(self):
    for tag in ["Kigo", "Num"]:
      if self.info.get(tag, None) is not None:
        self.info[tag] = (self.info[tag].strip("・")
                          .strip("-")
                          .replace(".", ""))
        if ("(" in self.info[tag] and ")" not in self.info[tag]) or "()" in self.info[tag]:
          self.info[tag] = self.info[tag][:self.info[tag].index("(")]

  def _handle_hknjanum(self, texts: List[List[Any]]):
    """Fallback handling when the corresponding finder cannnot extract HknjaNum.
    
    Args:
      texts: OCR results in a list.
    """
    if self.info.get("HknjaNum", None) is not None: return
    for line in texts[-2:]:
      
      res = get_insurer_num(line[-1])
      
      if res:
        self.info["HknjaNum"] = res
        break
    if self.info.get("HknjaNum", None) is not None: return
    for line in texts:
      if line[-1].isdigit() and (len(line[-1]) == 8 or len(line[-1]) == 6):
        self.info["HknjaNum"] = line[-1]
        break

  def _trim_hknjanum(self, texts: List[List[Any]]):
    """Truncates extracted HkanjaNum when necessary.

    Args:
      texts: OCR results in a list.
    """
    num = self.info.get("HknjaNum", None)
    if num is None: return
    if len(num) < 7: return
    all_text = "".join([l[-1] for l in texts])
    if "国民健康保険" in all_text:
      self.info["HknjaNum"] = num[:6]
    else:
      self.info["HknjaNum"] = num[:8]
  
  def _get_SkkGetYmd(self, texts: List[List[Any]]):
    """Truncates extracted HkanjaNum when necessary. 

    Args:
      texts: OCR results in a list.
    """
    num = self.info.get("SkkGetYmd", None)
    if num is not None: return

    for txt in texts:
      
      ret,text = skkget_match(txt[-1])
      # print('199: ',ret,text)
      if ret:
        status =  self._Check_two_data_in_one_line(text)
        if status:
          self.info['SkkGetYmd'] = str(min(int(status[0]),int(status[1])))
          return
          
        skk=get_date(text)
        if skk:
          # if self.info.get('SkkGetYmd',None):
          #   break
          self.info['SkkGetYmd'] = str(skk[0])

    if self.info.get("SkkGetYmd", None):
      pass
    else:
      self.info['SkkGetYmd'] = None
    

  def _get_HonKzkKbn(self, texts: List[List[Any]]):
    key_words1 = ['家族', '被扶養者']
    key_words2 = ['本人']
#     print(len(self.info['HknjaNum']))
    if not self.info.get('HknjaNum',None):
      return
    all_txt = ''
    for txt in texts:
      all_txt = all_txt + txt[-1]
    for key_word in key_words1:
      if key_word in all_txt:
        self.info['HonKzkKbn'] = '家族'
        return
    for key_word in key_words2:
      if key_word in all_txt:
        self.info['HonKzkKbn'] = '本人'
        return
    Hkn2keta = [
      '67',
      '06',
    ]
    for num in Hkn2keta:
      if len(self.info['HknjaNum']) == 6 or str(self.info['HknjaNum'])[0:2]==num:
        names = set()
        for i in texts:
          for key,key_finder in zip(HonKKEY,HonKKEY_FINDER):
            status = key.search(i[-1])
            try:
              if status:
                names.add(key_finder.findall(i[-1])[0].replace('氏名','').replace('主',''))
            except:
              print('no find name')
        names = list(names)
        if len(names) == 1:
          self.info['HonKzkKbn'] = '本人'
          return
        else:
          self.info['HonKzkKbn'] = '家族'
          return
    self.info['HonKzkKbn'] = '本人'
    return


  def _check_HKB_with_list(self, texts: List[List[Any]]):
    alltxts = "".join(i[-1] for i in texts)
    delete_list=['(',')','ミ']
    for t in delete_list:
      alltxts = alltxts.replace(t,'')
    for p in HknjaNum_LIST:
      if len(p) > 7:
        # pp = re.compile(p[:7].replace('1',''))
        pp = re.compile(p[:7])
      else:
        # pp = re.compile(p.replace('1',''))
        pp = re.compile(p)
      if pp.search(alltxts):
        self.info["HknjaNum"] = p
        return

  def _check_HKB_with_no_1_list(self, texts: List[List[Any]]):
    if self.info.get("HknjaNum",None):
      return
    alltxts = "".join(i[-1] for i in texts)
    delete_list=['1','(',')']
    for t in delete_list:
      alltxts = alltxts.replace(t,'')
    for p in HknjaNum_no_1_LIST:
      if len(p) > 7:
        pp = re.compile(p[:7].replace('1',''))
        # pp = re.compile(p[:7])
      else:
        pp = re.compile(p.replace('1',''))
        # pp = re.compile(p)
      if pp.search(alltxts):
        self.info["HknjaNum"] = p
        return


  def _check_Kigo_with_nashi(self):
    keywords = [
      '無',
      'し',
      'ノ',
      '/',
    ]
    if self.info.get('Kigo',None):
      for key in keywords:
        if key in self.info['Kigo']:
          self.info['Kigo'] = '無し'


  def _check_SkkGetYmd_and_Num_with_hknjanum_(self,texts):
    hkn = self.info.get("HknjaNum", None)
    if not hkn:
      return
    if not hkn[:2] == '28':
      return
    print(352)
    p = re.compile('注意?事?項{e<2}')
    for line in texts:
      if p.search(line[-1]):
        try:
          self.info['SkkGetYmd'] = get_date(line[-1])[0]
        except:
          self.info['SkkGetYmd'] = None
    
    p = re.compile('被保険者証(\d+)')
    for line in texts:
      if p.search(line[-1]):

        try:
          self.info['Num'] = p.findall(line[-1])[0]
        except:
          self.info['Num'] = None


  def _except_YukoEdYmd(self,texts):
    for line in texts:
      text = line[-1]
      if '有効' in text[-3:]:
        if get_date(text):
          self.info['YukoEdYmd'] = get_date(text)[0]
          return
    

  def _check_oneLine_have_YukoEdYmd_YukoStYmd_(self,texts):
    if self.info.get('YukoEdYmd', None) and self.info.get('YukoStYmd', None):
      return

    p = re.compile('年.+月.+日.+年.+月.+日')
    for line in texts:
      text = line[-1]
      if p.search(text):
        text = self._oneLine_have_YukoEdYmd_YukoStYmd_preprocess(text)
        print(191,text)
        date_p = re.compile('年.*?月.*?日')
        try:
          i = date_p.search(text).span()[1]
          st = text[:i]
          ed = text[i:]
          print(321,st,ed)
          self.info['YukoEdYmd'] = get_date(ed)[0]
          self.info['YukoStYmd'] = get_date(st)[0]
        except:
          print('not two date')


  def _oneLine_have_YukoEdYmd_YukoStYmd_preprocess(self,text):

    reiwa = re.compile(r'(令?和|令和?)')
    text = reiwa.sub('令和',text)
    space_ni_reiwa = re.compile(r'[^(令和|平成|昭和|明治)](\d+)年')
    if space_ni_reiwa.search(text):
        idx = space_ni_reiwa.search(text).span()[0]
        text = text[:idx+1] + '令和'+ text[idx+1:]
    return text

  
  def _Check_two_data_in_one_line(self,text):
    p = re.compile('年.+月.+日.+年.+月.+日')
    if p.search(text):
      date_p = re.compile('年.*?月.*?日')
      try:
        i = date_p.search(text).span()[1]
        st = text[:i]
        ed = text[i:]
        print(369,st,ed)
        print(get_date(ed)[0],get_date(st)[0])
        return [str(get_date(ed)[0]),str(get_date(st)[0])]
      except:
        print('not two date')
        return None
    return None
  