FROM nvidia/cuda:12.3.2-devel-ubuntu22.04

# Install dependencies
RUN apt-get update && apt-get install -y \
openssh-server \
sudo \
git \
python3 \
python3-pip \
python3-venv \
wget \
bzip2 \
ca-certificates \
curl \
vim \
&& rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -rm -d /home/ubuntu -s /bin/bash -g root -G sudo -u 1000 ubuntu
RUN echo 'ubuntu:ubuntu' | chpasswd

# Configure SSH and generate host keys
RUN mkdir /var/run/sshd && ssh-keygen -A

# Switch to root for SSH and leave user switching for runtime
WORKDIR /home/ubuntu

# Install Mambaforge in the user's mamba directory for bind mount
RUN wget -O Mambaforge.sh https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-Linux-x86_64.sh && \
bash Mambaforge.sh -b -p /home/ubuntu/miniforge3 && \
rm Mambaforge.sh

ENV PATH=/home/ubuntu/miniforge3/bin:$PATH
ENV MY_VARIABLE=some_value

# Expose SSH port
EXPOSE 22

# Start SSH service as root
CMD ["/usr/sbin/sshd", "-D"]

# Set the working directory
WORKDIR /home/ubuntu

# Initialise mamba shell
RUN mamba init

# Set user to non-root
RUN su - ubuntu