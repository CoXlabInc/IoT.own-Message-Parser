import base64
from datetime import datetime, timedelta

def post_process(message):
  raw = base64.b64decode(message['lora_meta']['raw'])
  print(f"[Accura3300e] raw:{raw}")
  return message

