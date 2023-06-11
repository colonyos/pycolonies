FROM ubuntu:22.04
WORKDIR /
RUN apt-get update; apt-get -y install python3 python3-pip
RUN pip3 install pycolonies
COPY libcryptolib.so /usr/local/lib
COPY fibonacci_executor.py /
CMD ["python3", "/fibonacci_executor.py"]
