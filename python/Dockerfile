# set base image (host OS)
FROM public.ecr.aws/bitnami/python:3.9-prod-debian-10

# set the working directory in the container
WORKDIR /code

# copy the dependencies file to the working directory
COPY requirements.txt .

# install dependencies
RUN pip install -r requirements.txt
RUN pip install lxml[html_clean]

# copy the content of the local src directory to the working directory
COPY src/ .


# command to run on container start
CMD [ "python", "./server.py" ]
