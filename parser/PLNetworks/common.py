import os
import base64
import json
import subprocess

ps = subprocess.Popen(['node', os.path.join(os.path.dirname(__file__), 'glue.js')], stdin=subprocess.PIPE, stdout=subprocess.PIPE)

def post_process(message):
    if message.get('lora_meta') is None or message['lora_meta'].get('raw') is None:
        print(f'[PLN] A message have no lora_meta.raw from Group ID:{message["grpid"]}, Node ID:{message["nid"]}')
        return message

    input_data = { "data": base64.b64decode(message['lora_meta']['raw']),
                   "node": message['device'],
                   "gateway": message['gateway'] }

    ps.stdin.write(json.dumps(input_data))
    ps.stdin.flush()
    
    return ps.stdout.readline()

if __name__ == '__main__':
    raw = 'VQABAF4CAKlsGOaWV4yPhsGsR4vDjeaWV4yPhu0Gklsje8IEZGJkZPABXQ=='

    test_input = '{"data":"' + raw + '","node":{},"gateway":{}}'
    ps.stdin.write(test_input.encode('ascii'))
    ps.stdin.flush()
    out = ps.stdout.readline()
    print(out)
    
