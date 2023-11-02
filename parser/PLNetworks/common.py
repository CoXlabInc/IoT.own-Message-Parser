import os
import base64
import json
import subprocess

ps = subprocess.Popen(['node', os.path.join(os.path.dirname(__file__), 'glue.js')], stdin=subprocess.PIPE, stdout=subprocess.PIPE)

def post_process(message, param=None):
    if message.get('meta') is None or message['meta'].get('raw') is None:
        print(f'[PLN] A message have no meta.raw from Group ID:{message["grpid"]}, Node ID:{message["nid"]}')
        return message

    input_data = { "data": message['meta']['raw'],
                   "node": message['device'],
                   "gateway": message['gateway'] }

    ps.stdin.write(json.dumps(input_data).encode('ascii'))
    ps.stdin.flush()
    
    result = ps.stdout.readline()
    print(result)
    
    result_dict = json.loads(result)
    for key in result_dict.keys():
    	message['data'][key] = result_dict[key]
    return message
    

if __name__ == '__main__':
    raw = 'VQABAF4CAKlsGOaWV4yPhsGsR4vDjeaWV4yPhu0Gklsje8IEZGJkZPABXQ=='

    test_input = '{"data":"' + raw + '","node":{},"gateway":{}}'
    ps.stdin.write(test_input.encode('ascii'))
    ps.stdin.flush()
    out = ps.stdout.readline()
    print(out)
