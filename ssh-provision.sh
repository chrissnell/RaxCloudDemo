#!/bin/bash

if [ ! -e ~/.ssh/id_*.pub ];
then
   echo "No SSH public key found.   Generating one now..."
   /usr/bin/ssh-keygen
else
   echo "SSH public key found."
fi
