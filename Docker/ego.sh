#!/bin/bash
/neo4j/bin/neo4j start
echo "Wait for neo4j start..."
sleep 5
cd /PyEGo
python PyEGo.py -p "$2" -r "$1"
