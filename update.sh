#!/bin/bash
OUTPUT="$(./get-wksdata.py)"
RRDUPDATE=`rrdtool update mks48II-1.rrd ${OUTPUT}`
./graph.sh
