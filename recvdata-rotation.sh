#! /bin/sh
YM=`date +\%Y\%m`
YMD=`date +\%Y\%m\%d`
PRG="/usr/local/bin/uecsrxd-insert.py"
ZIP="/usr/bin/zip -9 "
RM="/usr/bin/rm"
LOGD="/var/log/uecs"
LOGF="recvdata.log-"${YMD}
ARCF="recvdata.log-"${YM}".zip"
${PRG} ${LOGF}
${ZIP} ${LOGD}/${ARCF} ${LOGD}/${LOGF}
${RM} ${LOGD}/${LOGF}
