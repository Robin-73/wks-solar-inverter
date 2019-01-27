#!/bin/bash
export LC_CTYPE="fr_CH.UTF-8"

now=$(date +%s)
lasthour=$now-3600
last4h=$now-14400
lastday=$now-86400
lastweek=$now-604800
lastmonth=$now-18144000

rrdtool graph wks48ii-1.png -s $lastday -e $now \
	-w 785 -h 150 -a PNG \
	--slope-mode \
	--font DEFAULT:7: \
	--font TITLE:12:"Arial" \
	--font LEGEND:8:"DejaVu Sans Mono" \
	--title "Power Usage and Production" \
	--watermark "`date`" \
	--vertical-label "Power(W)" \
	--right-axis-label "charge-load(%)" \
	--x-grid MINUTE:10:HOUR:1:MINUTE:300:0:%R \
	--alt-y-grid --rigid \
	--color=BACK#C0C0C0 \
	--color=CANVAS#F0F0F0 \
	--color=SHADEB#666666 \
	DEF:pu=mks48II-1.rrd:pu:AVERAGE \
	DEF:ps=mks48II-1.rrd:ps:AVERAGE \
	DEF:bati=mks48II-1.rrd:bati:AVERAGE \
	DEF:batv=mks48II-1.rrd:batv:AVERAGE \
	CDEF:pc=pu,-1,*	\
	CDEF:pb=bati,batv,* \
	CDEF:pi=pu,ps,-,pb,- \
	COMMENT:"               " \
	COMMENT:"Current  " \
    	COMMENT:"Average  " \
	COMMENT:"Maximum  " \
        COMMENT:"Minimum \n" \
	COMMENT:"----------------------------------------------------------\n" \
	AREA:pc#99CCFF:"Power used\t"         \
	LINE:pc#66B2FF:         \
	GPRINT:pu:LAST:"%6.2lf %SW" \
	GPRINT:pu:AVERAGE:"%6.2lf %SW" \
	GPRINT:pu:MAX:"%6.2lf %SW" \
	GPRINT:pu:MIN:"%6.2lf %SW\n" \
	AREA:ps#FFFF00:"Solar prod\t"        \
	LINE:ps#999900:        \
	GPRINT:ps:LAST:"%6.2lf %SW" \
	GPRINT:ps:AVERAGE:"%6.2lf %SW" \
	GPRINT:ps:MAX:"%6.2lf %SW" \
	GPRINT:ps:MIN:"%6.2lf %SW\n" \
	AREA:pb#01F100:"Batt. prod\t"        \
	GPRINT:pb:LAST:"%6.2lf %SW" \
	GPRINT:pb:AVERAGE:"%6.2lf %SW" \
	GPRINT:pb:MAX:"%6.2lf %SW" \
	GPRINT:pb:MIN:"%6.2lf %SW\n" \
	AREA:pi#FF63471a:"Util. used\t"        \
	LINE:pi#8B0000:        \
	GPRINT:pi:LAST:"%6.2lf %SW" \
	GPRINT:pi:AVERAGE:"%6.2lf %SW" \
	GPRINT:pi:MAX:"%6.2lf %SW" \
	GPRINT:pi:MIN:"%6.2lf %SW\n" \
