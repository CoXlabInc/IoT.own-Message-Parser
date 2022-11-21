// -*- mode: js; js-indent-level: 2; -*-
var handler = require('./handler.js')

process.stdin.setEncoding('utf-8')
process.stdout.setEncoding('utf-8')
process.stdin.on('readable', () => {
  const input = process.stdin.read()
  if (!!input) {
    let out = {}
    let i = {}
    let decoded_data;
    try {
      i = JSON.parse(input)
      decoded_data = Buffer.from(i.data, 'base64')
    
      console.error(decoded_data)
    } catch(e) {
      console.error(e)
      console.log(JSON.stringify(out))
      return
    }

    try {
      out = handler.dataHandler(decoded_data, i.node, i.gateway)
    } catch(e) {
      console.error(e)
    }
    console.log(JSON.stringify(out))
  }
})
