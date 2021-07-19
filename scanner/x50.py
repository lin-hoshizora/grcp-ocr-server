"""
Controller for Plustek X50 Scanner

Guanqun Wang
"""
import cv2
from .scanner import Scanner
from .utils import crop, to_rgb
from . import scanpy


class X50(Scanner):
  """
  A class for Plustek X50
  """
  def __init__(self):
    print("Initializing Plustek X50...")
    self.in_warmup = False
    self.dev = scanpy.X50()
    self.auto_warm()
    buff = self.dev.scan()
    if not buff:
      raise ValueError('Scanner does not work!')
    img = to_rgb(buff)
    self.in_warmup = False
    cv2.imwrite('./scanner_bg.jpg', img[:, :, ::-1])

  def auto_warm(self):
    """
    Start warmup as soon as paper is detected
    :return:
    """
    if not self.in_warmup:
      self.in_warmup = True
      self.dev.warmup()

  def cancel(self):
    """
    Cancel during warmup
    :return:
    """
    if self.in_warmup:
      self.dev.cancel()
      self.in_warmup = False

  def scan(self):
    self.auto_warm()
    buff = self.dev.scan()
    if not buff:
      return None
    img = crop(to_rgb(buff))
    self.in_warmup = False
    return img

  def reconnect(self):
    """
    Cleanup and connect again
    :return:
    """
    self.dev.clean()
    self.dev.__init__()

  def __str__(self):
    print('Plustek X50')
