import unittest
import zipfile
from io import BytesIO
from typing import Dict
from zipfile import ZipFile

from compressors import ZIP_COMPRESSORS


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


if __name__ == '__main__':
    unittest.main()
