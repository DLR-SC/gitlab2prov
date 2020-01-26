FROM python:3

ADD gitlab2prov.py /
ADD gl2p/* /gl2p/
ADD requirements.txt /

ADD config/config.ini /config/

RUN pip install -r requirements.txt

CMD [ "python", "./gitlab2prov.py" ]