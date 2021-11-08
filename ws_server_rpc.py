import asyncio
import json
from pathlib import Path
import websockets
import yaml
import cv2
from utils import get_logger, get_timestamp, handle_err, handle_res
from docker_manager import DockerManager
from scanner import ScannerClient
from model_serving.client import ModelServerClient
from ocr2 import InsuranceReader
from ocr2.info_extractor import MainAnalyzer
from ocr2.info_extractor import MainAnalyzer,KouhiAnalyzer,KoureiAnalyzer


with open('config/api_config.yaml') as f:
  config = yaml.safe_load(f)
logger = get_logger(config['logger'])
data_folder = Path(config['websocket']['data_path'])
logger.info(f'Response JSON folder: {str(data_folder)}')
if not data_folder.exists():
  logger.warning(f'Response JSON folder {str(data_folder)} does not exist, created a new one.')
  logger.warning(f'{str(data_folder)} may be only accessible inside docker container if not manually exposed.')
  data_folder.mkdir(parents=True)

with open('config/api_err.yaml') as f:
  err = yaml.safe_load(f)

docker_manager = DockerManager(logger=logger)
scanner = ScannerClient(docker_manager=docker_manager,logger=logger)
model_server = ModelServerClient(docker_manager=docker_manager, logger=logger)
analyzers = {"主保険": MainAnalyzer(),"公費":KouhiAnalyzer(),'高齢受給者':KoureiAnalyzer(),'限度額認証':KoureiAnalyzer()}
reader = InsuranceReader(model_server=model_server, analyzers=analyzers, logger=logger)

def validate_json(msg):
  if 'Scan' in msg or 'Patient' in msg or 'Insurance' in msg or 'MyNumber' in msg or 'Test' in msg or 'Restart' in msg:
    return True
  return False

def scan(img_path, sess_id, err_save_path):
  img_path, scan_err = scanner.scan(img_path=img_path, sess_id=sess_id)
  if img_path is None or len(img_path) == 0:
    img_path = None
    scan_err = {'ErrCode': scan_err['ErrCode'], 'ErrMsg': scan_err['ErrMsg']}
    err_str = handle_err(scan_err, err_save_path, logger)
  else:
    err_str = None
  return img_path, err_str

async def serve_ocr(websocket, path):
  """
  Provide OCR service via websocket
  """
  async for data in websocket:
    sess_id = get_timestamp()
    test_save_path = data_folder / (sess_id + '_test.json')
    scan_save_path = data_folder / (sess_id + '_scan.json')
    info_save_path = data_folder / (sess_id + '_info.json')
    err_save_path = data_folder / (sess_id + '_err.json')
    restart_save_path = data_folder / (sess_id + '_restart.json')
    logger.info(f'Session ID: {sess_id}')
    logger.info(f'Websocket Received: {str(data)}')

    if not isinstance(data, str):
      err_str = handle_err(err['non-text'], err_save_path, logger)
      await websocket.send(err_str)
      continue

    try:
      json_req = json.loads(data)
    except json.JSONDecodeError:
      err_str = handle_err(err['non-json'], err_save_path, logger)
      await websocket.send(err_str)
      continue

    if not validate_json(json_req):
      err_str = handle_err(err['invalid-json'], err_save_path, logger)
      await websocket.send(err_str)
      continue

    if 'Restart' in json_req:
      model_server.restart()
      res_json = {"Cooldown": model_server.config["grpc"]["restart_cooldown"]}
      res_str = handle_res(res_json, restart_save_path, logger)
      await websocket.send(res_str)

    if 'Test' in json_req:
      if json_req['Test'] == 'Accelerator':
        res = model_server.infer_sync(sess_id=sess_id, network='Check', img=None)
        res_str = handle_res(res, test_save_path, logger)
        await websocket.send(res_str)
        continue
      else:
        err_str = handle_err(err['invalid-json'], err_save_path, logger)
        await websocket.send(err_str)
        continue

    if 'Scan' in json_req:
      if json_req['Scan'] in ['Insurance', 'MyNumber', 'Picture']:
        # insurance ocr
        logger.info(f'{json_req["Scan"]} scan started')
        img_path, err_str = scan(img_path=None, sess_id=sess_id, err_save_path=err_save_path)
        if img_path is None:
          await websocket.send(err_str)
          continue
        logger.info(f'{json_req["Scan"]} scan done')
        if json_req['Scan'] == 'Picture':
          res_json = {"ImagePath": img_path}
          res_str = handle_res(res_json, scan_save_path, logger)
          await websocket.send(res_str)
          continue
        else:
          my_number = json_req['Scan'] == 'MyNumber'
      else:
        # read local image file
        logger.info('Picture read started')
        img_path, err_str = scan(img_path=json_req['Scan'], sess_id=sess_id, err_save_path=err_save_path)
        if img_path is None:
          await websocket.send(err_str)
          continue
        logger.info('Picture read done')
        if 'Hint' in json_req:
          my_number = json_req['Hint'] == 'MyNumber'
        else:
          my_number = False

      tag = 'MyNumber' if my_number else 'Insurance'
      logger.info(f'{tag} OCR started')
      try:
        img = cv2.imread(img_path)[..., ::-1]
      except Exception as e:
        logger.error('Error during reading local image' + str(e))
        err_str = handle_err(err['read-err'], err_save_path, logger)
        await websocket.send(err_str)
        continue
      try:
        syukbn = reader.ocr_sync(sess_id=sess_id, img=img)
      except Exception as e:
        logger.error('Error during reading local image' + str(e))
        err_str = handle_err(err['ocr-err'], err_save_path, logger)
        await websocket.send(err_str)
        continue
      if isinstance(syukbn, dict):
        err_str = handle_err(syukbn, err_save_path, logger)
        await websocket.send(err_str)
        continue
      logger.info(f'{tag} OCR done')
      res = {"Category": "NA", "SyuKbn": syukbn, "ImagePath": img_path}
      res_str = handle_res(res, scan_save_path, logger)
      if hasattr(reader, 'texts'):
        logger.debug('texts:')
        for l in reader.texts:
          logger.debug(l[-1])
      await websocket.send(res_str)

    if 'Insurance' in json_req or 'Patient' in json_req:
      res_json = {}
      for meta_k, meta_v in json_req.items():
        if meta_k != 'Insurance' and meta_k != 'Patient':
          res_json[meta_k] = json_req[meta_k]
          continue
        res_json[meta_k] = {}
        for field in meta_v:
          if field == 'SyuKbn':
            res_json[meta_k][field] = json_req[meta_k][field]
          else:
            res_json[meta_k][field] = reader.extract_info(field)
          if not isinstance(res_json[meta_k][field], dict):
            res_json[meta_k][field] = {'text': res_json[meta_k][field], 'confidence': 1.0}
      res_json['CheckBirthday'] = True
      res_str = handle_res(res_json, info_save_path, logger)
      await websocket.send(res_str)


# start server(s)
ocr_ip = config['websocket']['ocr']['ip']
ocr_port = config['websocket']['ocr']['port']
logger.info(f'Start OCR server on {ocr_ip}:{ocr_port}')
ocr_server = websockets.serve(serve_ocr, ocr_ip, ocr_port)
asyncio.get_event_loop().run_until_complete(ocr_server)
asyncio.get_event_loop().run_forever()
