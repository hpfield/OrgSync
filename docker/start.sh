#!/bin/bash

# Start SSHD as root
/usr/sbin/sshd

# Switch to the ubuntu user and start an interactive shell or any other process
exec su - ubuntu
