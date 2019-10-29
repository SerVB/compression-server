# compression-server
## How to try?
Start the server by
```shell script
python server.py [PORT]
```

If you don't define a port, default one will be used.

Then you can compress some files using `curl`:
```shell script
curl -F "file=@/home/servb/PycharmProjects/compression-server/text.txt" http://localhost:8080/convert/zipLzma -o answer.zip
```

## Running tests
```shell script
python tests.py
```
