from flask import Flask
from flask import request
from flask import Response
from io import BytesIO
from flask import send_file, render_template
from compressors import ZipCompressor, ZipCompressorFactory, ZIP_COMPRESSOR_TYPES

app = Flask(__name__)

@app.route('/convert/<string:output_type>', methods=['POST'])
def handle_request(output_type):

    if not (output_type in ZIP_COMPRESSOR_TYPES):
        error = 'Format not supported'
        return Response('BAD_REQUEST: ' + error, 400)

    if (len(request.files) != 1):
        error = 'Single file should be sent'
        return Response('BAD_REQUEST: ' + error, 400)

    file_key = next(request.files.keys())
    if (len(request.files.getlist(file_key)) != 1):
        error = 'Single file should be sent'
        return Response('BAD_REQUEST: ' + error, 400)
    file = request.files[file_key]

    compressor = ZipCompressorFactory(ZIP_COMPRESSOR_TYPES[output_type]).create()
    compressor.create_archive()
    compressor.put(file_name=file_key, file_content=file.read())
    archive_content = compressor.get_archive_bytes()
    archive_name = compressor.add_extension(file_key)
    return send_file(BytesIO(archive_content), as_attachment=True, attachment_filename=archive_name)

@app.route('/')
@app.route('/toy.html')
def frontend():
    return render_template('toy.html')

if __name__ == '__main__':
    app.run()
