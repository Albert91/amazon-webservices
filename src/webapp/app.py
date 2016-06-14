import json
from uuid import uuid4

import boto3
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)
QUEUE_NAME = 'arek-album'
BUCKET_NAME = '159319-arek'
BUCKET_ADDRESS = 'https://s3.eu-central-1.amazonaws.com/159319-arek'


@app.route('/')
def index():
    return render_template('upload_form.html', uuid=uuid4().hex)


@app.route('/upload', methods=['POST'])
def upload():
    files = request.files
    uuid = request.form['uuid']
    album = {
        'photos': []
    }

    for f in files.getlist('file'):
        destination_filename = 'photos/%s/%s' % (uuid, f.filename)
        photo_url = '%s/%s' % (BUCKET_ADDRESS, destination_filename)

        album['photos'].append(photo_url)
        upload_s3(f, destination_filename)

    return jsonify(album)


def upload_s3(source_file, destination_filename):
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(BUCKET_NAME)
    bucket.put_object(Key=destination_filename, Body=source_file, ACL='public-read')


@app.route('/create-album', methods=['POST'])
def create_album():
    photos_count = len(request.form)
    photos_urls = []

    for i in range(0, photos_count - 2):
        key = 'photos_%s' % i
        photos_urls.append(request.form[key])

    sqs_object = {
        'email': request.form['email'],
        'photos': photos_urls
    }

    sqs = boto3.resource('sqs')
    queue = sqs.get_queue_by_name(QueueName=QUEUE_NAME)
    queue.send_message(MessageBody=json.dumps(sqs_object))

    return render_template('thank_you.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
