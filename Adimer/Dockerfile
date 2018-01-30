FROM python:2.7
ENV PYTHONUNBUFFERED 1
RUN mkdir /config
ADD ./config/requirements.txt /config/

RUN pip install -r /config/requirements.txt

RUN mkdir /app
WORKDIR /app
COPY ./adimer_backend ./adimer_backend
WORKDIR /app/adimer_backend
RUN chmod +x start.sh
RUN ls -l
