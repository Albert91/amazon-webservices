import json
import time
from cStringIO import StringIO

import boto3
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa

import config

sqs = boto3.resource('sqs')
albums = sqs.get_queue_by_name(QueueName=config.QUEUE_NAME)


def _create_pdf(pdf_data):
    stream = StringIO()
    pisa.CreatePDF(StringIO(pdf_data.encode('utf-8')), pdf)
    return stream


def _generate_html(photos):
    template = Environment(loader=FileSystemLoader('templates')).get_template('pdf_template.html')
    return template.render(photos=photos)


def _send_email(mailer, recipient, photo_urls):
    message = mailer.Message()
    message.From = "tomnow123456789@example.com"
    message.To = recipient
    message.Subject = "Your album is ready"
    message.Body = "Here is your album, enjoy!"
    message.attach("album.pdf", mimetype="application/pdf", content=_create_pdf(
        _generate_html(photo_urls)).getvalue())
    mailer = mailer.Mailer(
        host=config.MAIL_HOST, port=config.MAIL_PORT, use_tls=config.MAIL_TLS, usr=config.MAIL_TLS,
        pwd=config.MAIL_PASSWORD, use_ssl=config.MAIL_SSL)
    mailer.send(message)
    print "Sent"


while True:
    for album in albums.receive_messages():
        sqs_object = json.load(album.body.read())
        pdf = _create_pdf(_generate_html(sqs_object['photos']))
        _send_email(sqs_object['email'], pdf)
        album.delete()

    time.sleep(1)
