#!/bin/bash
echo "Running..."
pkill -F /home/austin/Documents/MemersMarkov/logs/pid.pid
/usr/bin/python3.6 -u /home/austin/Documents/MemersMarkov/memers_markov.py >> /home/austin/Documents/MemersMarkov/logs/log.log 2>&1 &
echo $! > /home/austin/Documents/MemersMarkov/logs/pid.pid
