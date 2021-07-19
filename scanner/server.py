from concurrent import futures
import logging
import asyncio
import json
import os
from pathlib import Path
import grpc
import yaml
import numpy as np
import cv2
from google.protobuf.struct_pb2 import Struct

from . import scanner_pb2
from . import scanner_pb2_grpc
from .x50 import X50
from .utils import get_logger, get_timestamp, get_scanner


class Scanner(scanner_pb2_grpc.ScannerServicer):
  def __init__(self, config):
    super().__init__()
    with open('config/scanner_err.yaml') as f:
      self.err = yaml.safe_load(f)
    self.config = config
    self.logger = get_logger(config['logger'])
    self.scanner, self.data_folder = get_scanner(config['scanner'], X50)
    if self.scanner is None:
      self.logger.info('Skip scanner initialization, only local image is accepted as input.')

  def _scan(self, sess_id):
    save_path = str(self.data_folder / (sess_id + '.jpg'))
    img = self.scanner.scan()
    if not isinstance(img, np.ndarray):
      err = self.err['scan_err']
      self.logger.error(f'[{err["ErrCode"]}] Scanner returned a {type(img)}, expected np.ndarray. (Session ID: {sess_id})')
      return None, err

    ret = cv2.imwrite(save_path, img[..., ::-1])
    if not ret:
      err = self.err['save_err']
      self.logger.error(f'[{err["ErrCode"]}] Failed to save image to {str(save_path)}. (Session ID: {sess_id})')
      return None, err
    err = self.err['ok']
    return save_path, err

  def _read(self, sess_id, img_path):
    save_path = self.data_folder / (sess_id + '.jpg')
    img = cv2.imread(img_path)
    if not isinstance(img, np.ndarray):
      err = self.err['read_err']
      self.logger.error(f'[{err["ErrCode"]}] Failed to read image from {img_path}. (Session ID: {sess_id})')
      return None, err
    err = self.err['ok']
    return img_path, err

  def Scan(self, request, context):
    path, err_dict = self._scan(sess_id=request.sess_id)
    err = Struct()
    err.update(err_dict)
    res = scanner_pb2.ScanResponse(sess_id=request.sess_id, img_path=path, err=err)
    return res

  def test(self, sess_id, img_path):
    return img_path, {"test": "haha"}

  def Read(self, request, context):
    path, err_dict = self._read(sess_id=request.sess_id, img_path=request.img_path)
    err = Struct()
    err.update(err_dict)
    res = scanner_pb2.ScanResponse(sess_id=request.sess_id, img_path=path, err=err)
    return res

def serve():
  logging.basicConfig()
  with open('config/scanner_config.yaml') as f:
    config = yaml.safe_load(f)
  max_workers = config['grpc'].get('max_workers', 1)
  max_concurrent_rpcs = config['grpc'].get('max_concurrent_rpcs', None)
  server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers),
                       maximum_concurrent_rpcs=max_concurrent_rpcs)
  scanner_pb2_grpc.add_ScannerServicer_to_server(Scanner(config), server)
  ip = config['grpc'].get('ip', '127.0.0.1')
  port = config['grpc'].get('port', 50051)
  server.add_insecure_port(f'{ip}:{port}')
  server.start()
  server.wait_for_termination()

if __name__ == "__main__":
  serve()
