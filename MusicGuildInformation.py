from dataclasses import dataclass
from typing import List
@dataclass
class GuildInformation:
  def __init__(self):
    self.names : List[str] = []
    self.queue : List[str] = []
    self.looping = False
    self.loop_songs = 0
    self.message = None
    self.done = True



