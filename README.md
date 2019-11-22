[![Python 3](https://img.shields.io/badge/python-3-blue.svg)](https://www.python.org/download/releases/2.7.7/)
[![Build status](https://github.com/SerVB/compression-server/workflows/tests/badge.svg)](https://github.com/SerVB/compression-server/actions)
# compression-server
## How to try?
Start the server by (5000 is a default one)
```shell script
export FLASK_APP=flask_server.py
python -m flask run (-p [PORT])
```

If you don't define a port, default one will be used.

Then you can compress some files using `curl`:
```shell script
curl -F "file=@/home/servb/PycharmProjects/compression-server/text.txt" http://localhost:[PORT]/convert/zipLzma -o answer.zip
```

## Running tests
```shell script
python tests.py
```
