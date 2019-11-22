import os
import subprocess
import time
import unittest
from http.server import HTTPServer
from io import BytesIO
from threading import Thread
from typing import Optional
from multiprocessing import Process
from zipfile import ZipFile
from flask_server import app

from compressors import ZIP_COMPRESSOR_TYPES, ZipCompressorFactory
from server import CompressionHTTPRequestHandler


# noinspection DuplicatedCode
class TestCompressors(unittest.TestCase):

    def setUp(self):
        pass

    def test_putting_unavailable_after_getting_archive_bytes(self):
        data = b"abcba31" * 100500
        filename = "test-file-name5434"
        for name, compression_type in ZIP_COMPRESSOR_TYPES.items():
            compressor = ZipCompressorFactory(compression_type).create()
            compressor.create_archive()
            compressor.put(filename, data)
            compressor.get_archive_bytes()
            with self.assertRaises(BaseException):
                compressor.put(filename + "1", data)

    def test_getting_unavailable_after_getting_archive_bytes(self):
        data = b"abcba3" * 100500
        filename = "test-file-name31231"
        for name, compression_type in ZIP_COMPRESSOR_TYPES.items():
            compressor = ZipCompressorFactory(compression_type).create()
            compressor.create_archive()
            compressor.put(filename, data)
            compressor.get_archive_bytes()
            with self.assertRaises(BaseException):
                compressor.get_archive_bytes()

    def test_file_set_in_archive(self):
        data = b"abcba1" * 100500
        filename = "test-file-name321"
        for name, compression_type in ZIP_COMPRESSOR_TYPES.items():
            compressor = ZipCompressorFactory(compression_type).create()
            compressor.create_archive()
            compressor.put(filename, data)
            archive_bytes = compressor.get_archive_bytes()
            bytes_io = BytesIO()
            bytes_io.write(archive_bytes)

            archive_file = ZipFile(bytes_io, mode="r", compression=compressor.compression_type)
            self.assertSetEqual(frozenset(archive_file.namelist()), {filename})

    def test_correct_compression_via_decompression(self):
        data = b"abcba3" * 100500
        filename = "test-file-name21"
        for name, compression_type in ZIP_COMPRESSOR_TYPES.items():
            compressor = ZipCompressorFactory(compression_type).create()
            compressor.create_archive()
            compressor.put(filename, data)
            archive_bytes = compressor.get_archive_bytes()
            bytes_io = BytesIO()
            bytes_io.write(archive_bytes)

            archive_file = ZipFile(bytes_io, mode="r", compression=compressor.compression_type)
            self.assertEqual(archive_file.read(filename), data)


def append_test_file_path(file_name: str) -> str:
    return "test-files/%s" % file_name


class TestFlaskServer(unittest.TestCase):
    server: Optional[Process] = None
    PORT = 8080

    def setUp(self):
        def run_server():
            app.run(host='127.0.0.1', port=self.PORT)
        self.server = Process(target=run_server)
        self.server.start()

    def tearDown(self):
        self.server.terminate()
        self.server.join()

    def test_file_savings(self):
        for file_name in ("text.txt", "text-empty.txt", "large-file.bin"):
            with open(append_test_file_path(file_name), "rb") as opened_file:
                file_content = opened_file.read()
                for compressor_name, compression_type in ZIP_COMPRESSOR_TYPES.items():
                    with open(os.devnull, "w") as null:
                        subprocess.run(
                            args='curl -F "{file_name}=@{dir}/{file}" http://localhost:{port}/convert/{type} -o {type}'.format(
                                dir=os.getcwd(),
                                file=append_test_file_path(file_name),
                                file_name = file_name,
                                port=self.PORT,
                                type=compressor_name,
                            ),
                            stdout=null,
                            stderr=null,
                            shell=True,
                        )

                    archive_file = ZipFile(compressor_name, mode="r", compression=compression_type)
                    archived_file_content = archive_file.read(file_name)
                    self.assertEqual(archived_file_content, file_content,
                                     msg="File %s, compressor %s" % (file_name, compressor_name))
                    os.remove(compressor_name)

    def test_simultaneous_requests(self):
        def request_archive(thread_return: list, file_name: str, compressor_name: str, compression_type: str,
                            thread_id: int):
            with open(append_test_file_path(file_name), "rb") as opened_file:
                file_content = opened_file.read()
                out_file = "%s-%s" % (compressor_name, thread_id)
                with open(os.devnull, "w") as null:
                    subprocess.run(
                        args='curl -F "{file_name}=@{dir}/{file}" http://localhost:{port}/convert/{type} -o {out}'.format(
                            dir=os.getcwd(),
                            file=append_test_file_path(file_name),
                            port=self.PORT,
                            file_name = file_name,
                            type=compressor_name,
                            out=out_file,
                        ),
                        stdout=null,
                        stderr=null,
                        shell=True,
                    )

                archive_file = ZipFile(out_file, mode="r", compression=compression_type)
                archived_file_content = archive_file.read(file_name)
                thread_return.append(archived_file_content == file_content)
                os.remove(out_file)

        requests_count = 2
        requests = list()

        for compressor_name, compression_type in ZIP_COMPRESSOR_TYPES.items():
            for thread_id in range(requests_count):
                for file_name in ("text.txt", "text-empty.txt", "large-file.bin"):
                    thread_return = list()
                    thread = Thread(target=request_archive,
                                    args=(
                                        thread_return,
                                        file_name,
                                        compressor_name,
                                        compression_type,
                                        len(requests),
                                    ))
                    thread_return.append(thread)

                    requests.append(thread_return)

        for request in requests:
            request[0].start()

        for request in requests:
            request[0].join()
            self.assertTrue(request[1])


# noinspection DuplicatedCode
class TestServer(unittest.TestCase):
    PORT = 8887
    httpd: Optional[HTTPServer] = None
    thread: Optional[Thread] = None

    def setUp(self):
        def create_server():
            with HTTPServer(("", self.PORT), CompressionHTTPRequestHandler) as httpd:
                self.httpd = httpd
                httpd.serve_forever()

        self.thread = Thread(target=create_server)
        self.thread.start()

        time.sleep(2)  # Give the server some time to start

    def tearDown(self):
        self.httpd.shutdown()
        self.thread.join()

    def test_file_savings(self):
        for file_name in ("text.txt", "text-empty.txt", "large-file.bin"):
            with open(append_test_file_path(file_name), "rb") as opened_file:
                file_content = opened_file.read()
                for compressor_name, compression_type in ZIP_COMPRESSOR_TYPES.items():
                    with open(os.devnull, "w") as null:
                        subprocess.run(
                            args='curl -F "file=@{dir}/{file}" http://localhost:{port}/convert/{type} -o {type}'.format(
                                dir=os.getcwd(),
                                file=append_test_file_path(file_name),
                                port=self.PORT,
                                type=compressor_name,
                            ),
                            stdout=null,
                            stderr=null,
                            shell=True,
                        )

                    archive_file = ZipFile(compressor_name, mode="r", compression=compression_type)
                    archived_file_content = archive_file.read(file_name)
                    self.assertEqual(archived_file_content, file_content,
                                     msg="File %s, compressor %s" % (file_name, compressor_name))
                    os.remove(compressor_name)

    def test_simultaneous_requests(self):
        def request_archive(thread_return: list, file_name: str, compressor_name: str, compression_type: str,
                            thread_id: int):
            with open(append_test_file_path(file_name), "rb") as opened_file:
                file_content = opened_file.read()
                out_file = "%s-%s" % (compressor_name, thread_id)
                with open(os.devnull, "w") as null:
                    subprocess.run(
                        args='curl -F "file=@{dir}/{file}" http://localhost:{port}/convert/{type} -o {out}'.format(
                            dir=os.getcwd(),
                            file=append_test_file_path(file_name),
                            port=self.PORT,
                            type=compressor_name,
                            out=out_file,
                        ),
                        stdout=null,
                        stderr=null,
                        shell=True,
                    )

                archive_file = ZipFile(out_file, mode="r", compression=compression_type)
                archived_file_content = archive_file.read(file_name)
                thread_return.append(archived_file_content == file_content)
                os.remove(out_file)

        requests_count = 2
        requests = list()

        for compressor_name, compression_type in ZIP_COMPRESSOR_TYPES.items():
            for thread_id in range(requests_count):
                for file_name in ("text.txt", "text-empty.txt", "large-file.bin"):
                    thread_return = list()
                    thread = Thread(target=request_archive,
                                    args=(
                                        thread_return,
                                        file_name,
                                        compressor_name,
                                        compression_type,
                                        len(requests),
                                    ))
                    thread_return.append(thread)

                    requests.append(thread_return)

        for request in requests:
            request[0].start()

        for request in requests:
            request[0].join()
            self.assertTrue(request[1])


if __name__ == '__main__':
    unittest.main()
