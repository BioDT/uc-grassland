# Stage 1: Dependencies
FROM python:3.12-slim-bookworm AS dependencies

RUN apt-get update && apt-get install -y \
    git \
    cmake \
    build-essential \
    libeigen3-dev \
    libboost-all-dev \
    gdal-bin \
    libgdal-dev \
    libgsl-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install ecCodes from source (version 2.39.0 or higher)
WORKDIR /tmp
RUN wget https://confluence.ecmwf.int/download/attachments/45757960/eccodes-2.39.0-Source.tar.gz && \
    tar -xzf eccodes-2.39.0-Source.tar.gz && \
    mkdir eccodes-build && cd eccodes-build && \
    cmake -DCMAKE_INSTALL_PREFIX=/usr/local ../eccodes-2.39.0-Source && \
    make -j$(nproc) && \
    make install && \
    ldconfig && \
    cd / && rm -rf /tmp/eccodes-*

# Set environment variables for ecCodes
ENV LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
ENV PATH=/usr/local/bin:$PATH

RUN pip install cfgrib eccodes

# Stage 2: Main simulation installation
FROM dependencies AS simulation

WORKDIR /

RUN git clone --depth 1 --branch unix https://github.com/BioDT/uc-grassland-model.git

WORKDIR /uc-grassland-model/build 
RUN cmake .. && make

RUN pip install git+https://github.com/BioDT/uc-grassland.git@gdal-nodatavalue-fix

WORKDIR /uc-grassland-model/

COPY run_pipeline_uc_grassland.sh /uc-grassland-model/run_pipeline_uc_grassland.sh
RUN chmod +x /uc-grassland-model/run_pipeline_uc_grassland.sh
CMD ["/uc-grassland-model/run_pipeline_uc_grassland.sh"]