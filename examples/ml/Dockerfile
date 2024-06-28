FROM colonyos/notebook:v1.0.15

RUN apt-get update && apt-get install -y python3 python3-pip wget vim git fish libgl1-mesa-glx libglib2.0-0
RUN python3 -m pip install --upgrade pip
RUN pip3 install pycolonies opencv-python tqdm Pillow scikit-learn keras matplotlib numpy

ENV PATH="$PATH:/root/go/bin" 
RUN cd /root; wget https://go.dev/dl/go1.21.6.linux-amd64.tar.gz; tar -xzf go1.21.6.linux-amd64.tar.gz;git clone https://github.com/colonyos/colonies.git; cd colonies; make; make install

COPY ./ml_executor.py /ml/ml_executor.py
COPY ./weights_unet100.h5 /ml/weights_unet100.h5

ENTRYPOINT ["python3", "/ml/ml_executor.py"]
