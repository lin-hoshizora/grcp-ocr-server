"""
Script used for simple manual testing
"""
import logging
import time
import grpc
import yaml

from utils import get_timestamp
import scanner_pb2
import scanner_pb2_grpc

def run(port, img_path, timeout):
  sess_id = get_timestamp()
  with grpc.insecure_channel('localhost:50051') as channel:
    stub = scanner_pb2_grpc.ScannerStub(channel)
    try:
      if img_path is None:
        req = scanner_pb2.ScanRequest(sess_id=sess_id)
        #res = stub.Scan(req, timeout=timeout)
        res = stub.Scan(req)
      else:
        req = scanner_pb2.ReadRequest(sess_id=sess_id, img_path=img_path)
        res = stub.Read(req, timeout=timeout)
      img_path = res.img_path
      err_str = res.err
      print(img_path, err_str)
      #if err_str['ErrCode'] is None:
      #  print(f'Scan succeeded! Image path: {img_path}.')
      #else:
      #  print(err_str)
    except grpc._channel._InactiveRpcError as e:
      print('Timeout!')

if __name__ == '__main__':
  with open('scanner_config.yaml') as f:
    config = yaml.safe_load(f)

  logging.basicConfig()
  port = config['grpc'].get('port', 50051)
  timeout = config['grpc'].get('timeout', 4)

  t0 = time.time()
  run(port, 'test.jpg', timeout)
  print(f'Time consumption of reading local image: {time.time() - t0 :.2f}s')

  t0 = time.time()
  run(port, None, timeout)
  print(f'Time consumption of scanning a new image: {time.time() - t0 :.2f}s')
