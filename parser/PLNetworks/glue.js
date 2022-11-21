// -*- mode: js; js-indent-level: 2; -*-
var handler = require('./handler.js')

process.stdin.setEncoding('utf-8')
process.stdout.setEncoding('utf-8')
process.stdin.on('readable', () => {
  const input = process.stdin.read()
  if (!!input) {
    i = JSON.parse(input)
    console.error(i.data)

    decoded_data = Buffer.from(i.data, 'base64')
    
    console.error(decoded_data)

    let out = {}
    try {
      out = handler.dataHandler(decoded_data, i.node, i.gateway);
    } catch(e) {
      console.error(e);
    }
    console.log(JSON.stringify(out))
  }
})
