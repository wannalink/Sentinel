FROM python:3.8
WORKDIR /ds-sentinel
COPY requirements.txt /ds-sentinel/
RUN pip install -r requirements.txt
COPY . /ds-sentinel
CMD python app.py