FROM python:3.11

WORKDIR /app

RUN pip install --upgrade pip

ADD requirements.txt .

RUN pip install -r requirements.txt

# Let the container hangs so we can access it using VSCode Remote Explorer
# And run scripts from within the container
ENTRYPOINT [ "tail", "-f", "/dev/null" ]
