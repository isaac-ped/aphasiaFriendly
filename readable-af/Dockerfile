FROM python:3.12
RUN mkdir /app
WORKDIR /app
RUN apt-get update && apt-get -y install pandoc
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt
COPY readable_af /app/readable_af
EXPOSE 8080
CMD ["gunicorn", "readable_af.rest:app"]
