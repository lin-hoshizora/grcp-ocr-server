import time
import docker

class DockerManager:
  def __init__(self, logger):
    self.client = docker.from_env()
    self.logger = logger

  def _get_container(self, img_name):
    for c in self.client.containers.list():
      if c.attrs['Config']['Image'] == img_name:
        return c

  def stop(self, img_name):
    c = self._get_container(img_name)
    if c is not None:
      self.logger.info(f"Stopping {c.attrs['Config']['Image']}...")
      c.stop()

  def restart(self, img_name, cooldown):
    c = self._get_container(img_name)
    if c is not None:
      self.logger.info(f"Restarting {c.attrs['Config']['Image']}...")
      c.restart()
      time.sleep(cooldown)

  def run(self, cooldown, **kwargs):
    self.logger.info(f"Running {kwargs.get('image', None)}...")
    c = self.client.containers.run(**kwargs)
    time.sleep(cooldown)

  def run_if_not_yet(self, cooldown, **kwargs):
    img_name = kwargs.get('image', None)
    matched = [c for c in self.client.containers.list() if c.status=='running' and c.attrs['Config']['Image'] == img_name]
    if len(matched) > 0:
      self.logger.info(f"{img_name} is already running, skip launch")
      return
    self.run(cooldown, **kwargs)
