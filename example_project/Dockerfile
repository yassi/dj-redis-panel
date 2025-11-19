FROM python:3.9

WORKDIR /app

# Copy requirements from root
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt
RUN pip install -e .

# Copy entire project
COPY . /app/
