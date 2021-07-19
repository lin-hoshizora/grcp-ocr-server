import time
import yaml
import grpc
from .utils import get_timestamp
from . import scanner_pb2
from . import scanner_pb2_grpc

class ScannerClient:
  def __init__(self, docker_manager, logger):
    with open('config/scanner_config.yaml') as f:
      self.config = yaml.safe_load(f)
    with open('config/scanner_err.yaml') as f:
      self.err = yaml.safe_load(f)
    self.logger = logger
    self.docker_manager = docker_manager
    self.docker_manager.run_if_not_yet(cooldown=self.config['grpc'].get('cooldown', 1), **self.config['docker'])

  def scan(self, img_path=None, sess_id=None):
    ip = self.config['grpc'].get('ip', 'localhost')
    port = self.config['grpc']['port']
    timeout = self.config['grpc']['timeout']
    self.logger.debug(f'ip: {ip}, port: {port}, timeout: {timeout}')
    if sess_id is None:
      sess_id = get_timestamp()
    for trial_idx in range(self.config['grpc']['max_trials']):
      with grpc.insecure_channel(f'{ip}:{port}') as channel:
        stub = scanner_pb2_grpc.ScannerStub(channel)
        try:
          if img_path is None:
            req = scanner_pb2.ScanRequest(sess_id=sess_id)
            res = stub.Scan(req, timeout=timeout)
          else:
            req = scanner_pb2.ReadRequest(sess_id=sess_id, img_path=img_path)
            res = stub.Read(req, timeout=timeout)
          img_path = res.img_path
          err = res.err
        except grpc._channel._InactiveRpcError as e:
          img_path = None
          err = self.err['scan_err']
      if img_path is None:
        self.logger.warning(f"Scanner failed: {trial_idx + 1}")
        self.restart()
        continue
      return img_path, err
    return img_path, err

  def restart(self):
    self.docker_manager.stop(self.config['docker']['image'])
    self.docker_manager.run_if_not_yet(cooldown=self.config['grpc'].get('cooldown', 1), **self.config['docker'])

