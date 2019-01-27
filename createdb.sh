#!/bin/bash
rrdtool create mks48II-1.rrd --start 1546334638 \
        DS:pu:GAUGE:600:U:U       \
	DS:ps:GAUGE:600:U:U       \
	DS:bati:GAUGE:600:U:U     \
	DS:batv:GAUGE:600:U:U      \
	RRA:AVERAGE:0.5:1:600      \
	RRA:AVERAGE:0.5:6:700      \
	RRA:AVERAGE:0.5:24:775     \
	RRA:AVERAGE:0.5:288:797    \
	RRA:MIN:0.5:1:600           \
	RRA:MIN:0.5:6:700          \
	RRA:MIN:0.5:24:775         \
	RRA:MIN:0.5:288:797        \
        RRA:MAX:0.5:1:600          \
	RRA:MAX:0.5:6:700          \
	RRA:MAX:0.5:24:775         \
	RRA:MAX:0.5:288:797
