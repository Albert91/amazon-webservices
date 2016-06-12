import json
from uuid import uuid4

import boto3
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)
QUEUE_NAME = 'arek-album'
BUCKET_NAME = '159319-arek'


@app.route('/')
def index():
    return render_template('upload_form.html', uuid=uuid4().hex)


@app.route('/upload', methods=['POST'])
def upload():
    files = request.files
    uuid = request.form['uuid']

    for f in files.getlist('file'):
        upload_s3(f, uuid)

    return jsonify()


def upload_s3(source_file, uuid):
    destination_filename = 'photos/%s/%s' % (uuid, source_file.filename)

    s3 = boto3.resource('s3')
    bucket = s3.Bucket(BUCKET_NAME)
    bucket.put_object(Key=destination_filename, Body=source_file)


@app.route('/remove-file', methods=['POST'])
def remove_file():
    object_key = 'photos/%s/%s' % (request.form['uuid'], request.form['filename'])

    s3 = boto3.resource('s3')
    bucket = s3.Bucket(BUCKET_NAME)
    bucket.delete_object(object_key)

    return jsonify()


@app.route('/create-album', methods=['POST'])
def create_album():
    sqs = boto3.resource('sqs')
    queue = sqs.get_queue_by_name(QueueName=QUEUE_NAME)

    sqs_object = {
        'email': request.json['email'],
        'photos': []
    }

    s3 = boto3.resource('s3')
    bucket = s3.Bucket(BUCKET_NAME)

    objects_list = list(bucket.list('photos/' + request.json['uuid'], '/'))
    sqs_object['photos'] = objects_list

    response = queue.send_message(MessageBody=json.dumps(sqs_object))

    return jsonify()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
