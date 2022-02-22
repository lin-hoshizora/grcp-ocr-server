"""Analyzer that extracts key information from OCR resutls of 公費保険"""
from distutils.errors import LibError
from pydoc import text
from sre_parse import DIGITS
from typing import List, Any
from unicodedata import digit
from .finders import JgnGakFinder, RouFtnKbnFinder
from .match import kohi_num_match, insurer_match
from .extract import get_date
from .re_pattern import KIGO, PURE_NUM
from .analyzer_base import AnalyzerBase
import regex as re
from .HknjaNum_list import HknjaNum_LIST,HknjaNum_no_1_LIST



date_tags = [
    "入院",
    "入院外",
    "外来",
    "通院",
    "調剤",
    "無",
    "1割"
]


class KouhiAnalyzer(AnalyzerBase):
  """Analyzer to extract key information from OCR results of 公費保険証.

  It tries to extract as much keyinformation as possible when `fit` is called.
  The input argument `texts` of `fit` is a list containing OCR results, each
  element of which also has to be a list, whose last element has to be text of
  one line. 

  All extracted information is stored in info, and can be queried by tag via
  `get`.

  Typical usage example:
    >>> analyzer = MainAnalyzer()
  """
  def __init__(self):
    config = {
        "HknjaNum": "wide_finder",
        "Num": "simple_finder", 
        ("Birthday", "YukoStYmd", "YukoEdYmd", "KofuYmd"): "dates_finder",
        "JgnGak": JgnGakFinder(),
        "RouFtnKbn": RouFtnKbnFinder(),
    }
    super().__init__(config)

  def fit(self, texts):
    self._preprocess(texts)
    self._finder_fit(texts)
    self._handle_nums(texts)
    self._handle_kigo(texts)
    self._handle_multi_dates(texts)
    self._check_RouFtnKbn_wari()
    self._check_Kigo_with_nashi()
    self._check_only_num_keyword_(texts)
    self._check_HKB_with_list(texts)
    self._check_oneLine_have_two_date_(texts)
    self._except_Num()
    self._except_YukoStYmd_YukoEdYmd_(texts)

  def _preprocess(self,texts):
      #jgngak
    p = re.compile(r'自己負担(.*?)([\d]+)')
    for idx, line in enumerate(texts):      
      if p.search(line[-1]):
        texts[idx][-1] = p.sub(line[-1],line[-1]+'円')

  def _handle_nums(self, texts: List[List[Any]]):
    """Handles hknjanum and num on the same line.

    Args:
      texts: OCR results in a list.
    """
    if self._have("HknjaNum") and self._have("Num"): return
    for idx, line in enumerate(texts[:5]):
      ret1, _ = insurer_match(line[-1])
      ret2, _ = kohi_num_match(line[-1])
      if ret1 and ret2 and idx + 1 < len(texts):
        next_line = texts[idx + 1][-1]
        if next_line.isdigit():
          self.info["HknajaNum"] = next_line[:8]
          self.info["Num"] = next_line[8:]

  def _handle_kigo(self, texts):
    # special handling for kigo
    if self._have("Kigo"): return
    self.info["Kigo"] = None

    for line in texts:
      for pattern in KIGO:
        match = pattern.findall(line[-1])
        if match and match[0] is not None:
          self.info["Kigo"] = match[0]


  def _handle_multi_dates(self, texts: List[List[Any]]):
    """Handles multiple dates.

    Args:
      texts: OCR results in a list.
    """
    froms = []
    untils = []
    for idx, line in enumerate(texts):
      
      has_from = 'から' in line[-1] or (len(line[-1]) > 2 and line[-1][-2]) == "か"
  
      
      has_until = "迄" in line[-1] or "まで" in line[-1]
      if not has_from and not has_until: continue
      dates = get_date(line[-1])

      if has_from and has_until and len(dates) == 2:
        froms.append((idx, dates[0]))
        untils.append((idx, dates[1]))
        continue
      if has_from and len(dates) == 1:
        froms.append((idx, dates[0]))
      if has_until and len(dates) == 1:
        untils.append((idx, dates[0]))
    
    if not (len(untils) > 1 and len(froms) > 1): return
    new_st = ""
    new_ed = ""
    for (idx_f, date_f), (idx_u, date_u) in zip(froms, untils):
      start = max(0, idx_f - 2, idx_u - 2)
      end = min(len(texts) - 1, idx_f + 2, idx_u + 2)
      for cidx in range(start, end + 1):
        for tag in date_tags:
          if tag in texts[cidx][-1].replace("憮", "無"):
            new_st += tag + " " + str(date_f) + ";"
            new_ed += tag + " " + str(date_u) + ";"
            texts[cidx][-1].replace(tag, "")
    print(new_st,new_ed)
    if new_st and new_ed:
      self.info["YukoStYmd"] = new_st
      self.info["YukoEdYmd"] = new_ed

  def _check_RouFtnKbn_wari(self):
    if self.info.get('RouFtnKbn',None):
      if '割' in self.info['RouFtnKbn']:
        self.info['RouFtnKbn']=None

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


  def _check_only_num_keyword_(self,texts):
    if self.info.get('Num',None):
      return
    res=[None]
    num_p = re.compile(r'[^\d]?番号')
    digit_p = re.compile(r'[\d・-]+')
    for line in texts:
      if num_p.search(line[-1]):
        matched =  line[-1][num_p.search(line[-1]).span()[1]:]
        if num_p.search(line[-1]).group() == '番号':
          if digit_p.search(matched):
            res = digit_p.findall(matched)
    self.info['Num'] = res[0]
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
    delete_list=['1','(',')','ミ']
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

  def _check_oneLine_have_two_date_(self,texts):
    if self.info.get('YukoEdYmd', None) and self.info.get('YukoStYmd', None):
      return

    p = re.compile('年.+月.+日.+年.+月.+日')
    for line in texts:
      text = line[-1]
      if p.search(text):
        text = self._check_oneLine_have_two_date_preprocess(text)
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


  def _check_oneLine_have_two_date_preprocess(self,text):

    reiwa = re.compile(r'(令?和|令和?)')
    text = reiwa.sub('令和',text)
    space_ni_reiwa = re.compile(r'[^(令和|平成|昭和|明治)](\d+)年')
    if space_ni_reiwa.search(text):
        idx = space_ni_reiwa.search(text).span()[0]
        text = text[:idx+1] + '令和'+ text[idx+1:]
    return text


  def _except_Num(self):
    if self.info.get('Num',None):
      DIGIT = re.compile(r'[^\d]')
      self.info['Num'] = DIGIT.sub('',self.info['Num']) 

  
  def _except_YukoStYmd_YukoEdYmd_(self,texts):
    if self.info.get("YukoStYmd",None) and self.info.get("YukoEdYmd",None):
      return
    p = re.compile('有効期間{e<2}')
    for idx,x in enumerate(texts):
      if p.search(x[-1]):
        for i in [idx-1,idx,idx+1]:
          print(251,texts[i][-1])
          if get_date(texts[i][-1]):
            if not self.info.get("YukoStYmd",None):
              self.info['YukoStYmd'] = get_date(texts[i][-1])[0]
            else:
              self.info['YukoEdYmd'] = get_date(texts[i][-1])[0]
              return