FROM python:3.6

#ADD my_script.py /
ADD . /code
WORKDIR /code

#RUN pip install pystrich

ENTRYPOINT [ "python", "./swarm.py", "7000", "root:7000" ]
