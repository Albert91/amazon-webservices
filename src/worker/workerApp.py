import time
from cStringIO import StringIO

import boto3
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa

from src import config

sqs = boto3.resource('sqs')
albums = sqs.get_queue_by_name(QueueName='arek-album')

# TODO: Set proper queue and JSON object for function
while True:
    for message in albums.receive_messages(MessageAttributeNames=['Author']):
        author_name = message.message_attributes.get('Author').get('name')
        print('Message body: %s' % message.body)
        message.delete()
    time.sleep(1)


def _create_pdf(pdf_data):
    pdf = StringIO()
    pisa.CreatePDF(StringIO(pdf_data.encode('utf-8')), pdf)
    return pdf


def _generate_html(photos):
    template = Environment(loader=FileSystemLoader('templates')).get_template('pdf_template.html')
    return template.render(photos=photos)


def send_email(mailer, recipient, photo_urls):
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
