#!/bin/bash

# Install AWS SAM CLI
curl -L https://github.com/aws/aws-sam-cli/releases/latest/download/aws-sam-cli-linux-x86_64.zip -o aws-sam-cli-linux-x86_64.zip
unzip aws-sam-cli-linux-x86_64.zip -d sam-installation
sudo ./sam-installation/install

# Verify SAM installation
where sam
sam —version

# Install Python 3.10.14
wget https://www.python.org/ftp/python/3.10.14/Python-3.10.14.tgz
tar -xf Python-3.10.14.tgz
cd Python-3.10.14
./configure --enable-optimizations
sudo make altinstall

