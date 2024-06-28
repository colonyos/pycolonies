FROM colonyos/notebook:v1.0.15

RUN apt-get update && apt-get install -y python3 python3-pip wget vim git fish libgl1-mesa-glx libglib2.0-0
RUN python3 -m pip install --upgrade pip
RUN pip3 install pycolonies opencv-python tqdm Pillow scikit-learn keras matplotlib numpy

ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8
ENV LC_CTYPE=UTF-8
ENV TZ=Europe/Stockholm
ENV COLONYOS_DASHBOARD_URL="https://dashboard.colonyos.io"
ENV COLONIES_TLS="true"
ENV COLONIES_SERVER_TLS="true"
ENV COLONIES_SERVER_HOST="server.colonyos.io"
ENV COLONIES_SERVER_PORT="443"
ENV COLONIES_MONITOR_PORT="21120"
ENV COLONIES_MONITOR_INTERVAL="1"
ENV COLONIES_SERVER_PRVKEY="f7a09f288428bb317047b60a2a9d93d69be34c187b14960cb38ae7892927e344"
ENV COLONIES_DB_HOST="localhost"
ENV COLONIES_DB_USER="postgres"
ENV COLONIES_DB_PORT="50070"
ENV COLONIES_DB_PASSWORD="rFcLGNkgsNtksg6Pgtn9CumL4xXBQ7"
ENV COLONIES_COLONY_PRVKEY="1715123955587d093b759edb4ecd643fffa581911f5e3fe224a3d11ff51f888e"
ENV COLONIES_PRVKEY="9201993f916425ce8d1ee0fe3dd6585469ebb97fd691824150c728d20e048c20"
ENV COLONIES_COLONY_NAME="hpc"
ENV AWS_S3_ENDPOINT="s3.colonyos.io:443"
ENV AWS_S3_ACCESSKEY="ZbyK0MGWH0Xr3P1NXeaV"
ENV AWS_S3_SECRETKEY="v30R89DGTUp7WnMCr36ffvaUjKBowQpL99INyHHd"
ENV AWS_S3_REGION_KEY=""
ENV AWS_S3_BUCKET="hpc"
ENV AWS_S3_TLS="true"
ENV AWS_S3_SKIPVERIFY="false"

ENV PATH="$PATH:/root/go/bin" 
RUN cd /root; wget https://go.dev/dl/go1.21.6.linux-amd64.tar.gz; tar -xzf go1.21.6.linux-amd64.tar.gz;git clone https://github.com/colonyos/colonies.git; cd colonies; make; make install

COPY ./ml_executor.py /ml/ml_executor.py
COPY ./weights_unet100.h5 /ml/weights_unet100.h5

ENTRYPOINT ["python3", "/ml/ml_executor.py"]
