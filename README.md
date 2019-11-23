[![Python 3](https://img.shields.io/badge/python-3-blue.svg)](https://www.python.org/download/releases/2.7.7/)
[![Build status](https://github.com/SerVB/compression-server/workflows/tests/badge.svg)](https://github.com/SerVB/compression-server/actions)
# compression-server
## How to try? The flask server
Start the server by (5000 is the default one)
```shell script
export FLASK_APP=flask_server.py
python -m flask run (-p [PORT])
```
## How to try? The bycicle server
Start the server by (8080 is the default one)
```shell script
python server.py [PORT]
```

If you don't define a port, default one will be used.

Then you can compress some files using `curl`:
```shell script
curl -F "file=@/home/servb/PycharmProjects/compression-server/text.txt" http://localhost:[PORT]/convert/zipLzma -o answer.zip
```

## Accessing the flask server from browser.
Print localhost:[PORT] in your browser's address bar.

## Running tests
```shell script
python tests.py
```
