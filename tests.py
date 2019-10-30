import os
import subprocess
import time
import unittest
import zipfile
from http.server import HTTPServer
from io import BytesIO
from threading import Thread
from typing import Dict, Optional
from zipfile import ZipFile

from compressors import ZIP_COMPRESSORS
from server import CompressionHTTPRequestHandler


# noinspection DuplicatedCode
class TestCompressors(unittest.TestCase):
    ZIP_DECOMPRESSORS: Dict[str, int] = {
        "zipStored": zipfile.ZIP_STORED,
        "zipDeflate": zipfile.ZIP_DEFLATED,
        "zipBzip2": zipfile.ZIP_BZIP2,
        "zipLzma": zipfile.ZIP_LZMA,
    }

    def setUp(self):
        pass

    def test_compressors_match_decompressors(self):
        self.assertSetEqual(set(ZIP_COMPRESSORS.keys()), set(self.ZIP_DECOMPRESSORS.keys()))

    def test_compressors_match_decompressors_types(self):
        for name, compressor in ZIP_COMPRESSORS.items():
            compressor_type = compressor.compression_type
            decompressor_type = self.ZIP_DECOMPRESSORS[name]
            self.assertEqual(compressor_type, decompressor_type)

    def test_putting_unavailable_after_getting_archive_bytes(self):
        data = b"abcba31" * 100500
        filename = "test-file-name5434"
        for name, compressor in ZIP_COMPRESSORS.items():
            compressor.create_archive()
            compressor.put(filename, data)
            compressor.get_archive_bytes()
            with self.assertRaises(BaseException):
                compressor.put(filename + "1", data)

    def test_getting_unavailable_after_getting_archive_bytes(self):
        data = b"abcba3" * 100500
        filename = "test-file-name31231"
        for name, compressor in ZIP_COMPRESSORS.items():
            compressor.create_archive()
            compressor.put(filename, data)
            compressor.get_archive_bytes()
            with self.assertRaises(BaseException):
                compressor.get_archive_bytes()

    def test_file_set_in_archive(self):
        data = b"abcba1" * 100500
        filename = "test-file-name321"
        for name, compressor in ZIP_COMPRESSORS.items():
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
        for name, compressor in ZIP_COMPRESSORS.items():
            compressor.create_archive()
            compressor.put(filename, data)
            archive_bytes = compressor.get_archive_bytes()
            bytes_io = BytesIO()
            bytes_io.write(archive_bytes)

            archive_file = ZipFile(bytes_io, mode="r", compression=compressor.compression_type)
            self.assertEqual(archive_file.read(filename), data)


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
        for file_name in ("text.txt", "text-empty.txt"):
            with open(file_name, "r", encoding="UTF-8") as opened_file:
                file_content = opened_file.read()
                for compressor_name, compressor in ZIP_COMPRESSORS.items():
                    with open(os.devnull, "w") as null:
                        subprocess.run(
                            args='curl -F "file=@{dir}/{file}" http://localhost:{port}/convert/{type} -o {type}'.format(
                                dir=os.getcwd(),
                                file=file_name,
                                port=self.PORT,
                                type=compressor_name,
                            ),
                            stdout=null,
                            stderr=null,
                            shell=True,
                        )

                    archive_file = ZipFile(compressor_name, mode="r", compression=compressor.compression_type)
                    archived_file_content = archive_file.read(file_name).decode("UTF-8")
                    self.assertEqual(archived_file_content, file_content,
                                     msg="File %s, compressor %s" % (file_name, compressor_name))
                    os.remove(compressor_name)


if __name__ == '__main__':
    unittest.main()
