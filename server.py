import re
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

from compressors import ZIP_COMPRESSOR_TYPES, AbstractCompressor, ZipCompressorFactory

try:
    _PORT = int(sys.argv[1])
except (ValueError, IndexError):
    _PORT = 8080


def strip_http_headers(http_reply):
    p = http_reply.find(b'\r\n\r\n')
    if p >= 0:
        return http_reply[p + 4:]
    return http_reply


class SplittingHTTPRequestHandler(BaseHTTPRequestHandler):

    # noinspection PyShadowingBuiltins
    def log_message(self, format, *args):
        pass  # Disable logging

    # noinspection PyPep8Naming
    def do_POST(self):
        self._split_body()

    def _split_body(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)

        body_lines = body.split(b'\r\n')
        body_lines = body_lines[1:]  # remove this: --------------------------d540825227eb0374
        if len(body_lines[-1]) == 0:
            body_lines = body_lines[:-1]  # remove the last line if empty
        body_lines = body_lines[:-1]  # remove this: --------------------------d540825227eb0374--

        headers_end_index = body_lines.index(b'')
        if headers_end_index == -1:
            self._answer_no_headers_found()
            return

        headers = b'\r\n'.join(body_lines[:headers_end_index]).decode("UTF-8")
        file_content = b'\r\n'.join(body_lines[headers_end_index + 1:])

        self._parse_split_body(headers, file_content)

    def _parse_split_body(self, headers: str, file_content: bytes):
        pass

    def _answer_no_headers_found(self):
        self.send_response(400)
        self.end_headers()
        self.wfile.write(b'Error: no headers found in your request')


class CompressionHTTPRequestHandler(SplittingHTTPRequestHandler):

    def _parse_split_body(self, headers: str, file_content: bytes):
        found_names = re.findall('filename=\"(.+)\"', headers)

        if len(found_names) == 0:
            self._answer_no_filename_found()
            return

        file_name = found_names[0]

        self._parse_url(file_name, file_content)

    def _parse_url(self, file_name: str, file_content: bytes):
        split_path = self.path.split("/")
        if len(split_path) != 3:
            self._answer_bad_post_path()
            return

        empty, convert, output_type = split_path
        if empty != "" or convert != "convert":
            self._answer_bad_post_path()
            return

        if output_type not in ZIP_COMPRESSOR_TYPES:
            self._answer_bad_post_output_type(output_type)
            return

        compressor = ZipCompressorFactory(ZIP_COMPRESSOR_TYPES[output_type]).create()
        self._create_archive(compressor, file_name, file_content)

    def _create_archive(self, compressor: AbstractCompressor, file_name: str, file_content: bytes):
        compressor.create_archive()
        compressor.put(file_name, file_content)
        archive_bytes = compressor.get_archive_bytes()

        archive_name = compressor.add_extension(file_name)

        self._answer_archive_bytes(archive_name, archive_bytes)

    def _answer_archive_bytes(self, archive_name: str, archive_bytes: bytes):
        self.send_response(200)
        self.send_header('Content-Type', 'application/zip')
        self.send_header('Content-Disposition', 'attachment;filename=%s' % archive_name)
        self.end_headers()
        self.wfile.write(archive_bytes)

    def _answer_bad_post_path(self):
        self.send_response(404)
        self.end_headers()
        self.wfile.write(b'Error: bad path\n')

    def _answer_bad_post_output_type(self, output_type: str):
        self.send_response(400)
        self.end_headers()
        self.wfile.write(
            b"Error: bad output type ('%s'). Available: %s\n" % (
                output_type.encode("UTF-8"),
                str(set(ZIP_COMPRESSOR_TYPES.keys())).encode("UTF-8"),
            )
        )

    def _answer_no_filename_found(self):
        self.send_response(400)
        self.end_headers()
        self.wfile.write(b'Error: no filename header found in your request')


def main():
    with HTTPServer(("", _PORT), CompressionHTTPRequestHandler) as httpd:
        print("Serving at port", _PORT)
        httpd.serve_forever()


if __name__ == "__main__":
    main()
