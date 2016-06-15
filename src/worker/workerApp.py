import json
import time
import os
from cStringIO import StringIO
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import boto3
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa

import config

sqs = boto3.resource('sqs')
albums = sqs.get_queue_by_name(QueueName=config.QUEUE_NAME)
session = boto3.session.Session()
client = session.client('ses', region_name='eu-west-1')

def _create_pdf(pdf_data):
    pdf = StringIO()
    pisa.CreatePDF(StringIO(pdf_data.encode('utf-8')), pdf)
    return pdf


def _generate_html(photos):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    template = Environment(loader=FileSystemLoader(current_dir))

    return template.get_template('templates/pdf_template.html').render(
        photos=photos
    )


def _send_email(recipient, photo_urls):
    msg = MIMEMultipart()
    msg['Subject'] = 'Email subject'
    msg['From'] = 'skala.pawel@gmail.com'
    msg['To'] = recipient

    part = MIMEText('Here is yours Album!')
    msg.attach(part)

    part = MIMEApplication(_create_pdf(
        _generate_html(photo_urls)).getvalue())
    part.add_header('Content-Disposition', 'attachment', filename="album.pdf")
    msg.attach(part)
    client.send_raw_email(
        msg.as_string(),
        Source=msg['From'],
        Destination={
            'ToAddresses': [
                recipient,
            ]
        })


while True:
    for album in albums.receive_messages():
        sqs_object = json.loads(album.body)
        _send_email(sqs_object['email'], sqs_object['photos'])
        album.delete()
    time.sleep(1)
