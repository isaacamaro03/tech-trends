FROM python:3.8

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . .

RUN python3 init_db.py

EXPOSE 3111

CMD [ "python3", "app.py"]