FROM nvidia/cuda:12.3.2-devel-ubuntu22.04 

# Install necessary packages
RUN apt update && apt install openssh-server sudo git wget -y

# Add user 'ubuntu'
RUN useradd -rm -d /home/ubuntu -s /bin/bash -g root -G sudo -u 1000 ubuntu
RUN echo 'ubuntu:ubuntu' | chpasswd

# Start SSH service
RUN service ssh start

# Expose SSH port
EXPOSE 22

# Set SSH to run in the foreground
CMD ["/usr/sbin/sshd","-D"]

# Install Python, pip, and venv
RUN set -eux; \
    apt-get update; \
    apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
    ; \
    rm -rf /var/lib/apt/lists/*

RUN wget "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh" -O /tmp/miniforge.sh \
    && bash /tmp/miniforge.sh -b -p /opt/conda \
    && rm /tmp/miniforge.sh

# Set the working directory
WORKDIR /home/ubuntu/OrgSync

# Install the conda environment
RUN mamba create -f environment.yml -y

# Activate the environment and set it as the default environment
RUN echo "source ~/.bashrc" >> ~/.bash_profile \
    && echo "mamba activate orgsync" >> ~/.bashrc

USER ubuntu
