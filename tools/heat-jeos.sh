#!/bin/bash
# Build a JEOS image using OZ

exit_usage(){
    echo "Error : $1"
    echo "Usage $0 <tdl file> <image name>"
    echo "Note tdl file must be a valid Oz TDL"
    echo "Note image name must match the name defined in the TDL"
    exit 1
}

DISK_FORMAT="qcow2"
LIBVIRT_IMGDIR="/var/lib/libvirt/images"
DEBUG="-d 3"

if [ $# -ne 2 ]; then
    exit_usage "Insufficient arguments"
fi
TDLFILE=$1
TDLNAME=$2
LIBVIRT_XMLFILE="/tmp/${TDLNAME}_libvirtxml.$$"

# Sanity check user input
if [ ! -s "${TDLFILE}" ]
then
    exit_usage "${TDLFILE} does not exist or is empty"
fi

if ! grep -q ${TDLNAME} ${TDLFILE}; then
    exit_usage "${TDLNAME} not defined in ${TDLFILE}"
fi

if [ -e "${LIBVIRT_IMGDIR}/${TDLNAME}.dsk" ]; then
    exit_usage "${LIBVIRT_IMGDIR}/${TDLNAME}.dsk already exists, please remove then re-run"
fi

oz-install -u ${DEBUG} ${TDLFILE} -x ${LIBVIRT_XMLFILE}

DSKFILE="${LIBVIRT_IMGDIR}/${TDLNAME}.dsk"
FMTFILE="${LIBVIRT_IMGDIR}/${TDLNAME}.${DISK_FORMAT}"
qemu-img convert -c -O ${DISK_FORMAT} ${DSKFILE} ${FMTFILE}

if [ -f ${FMTFILE} ]; then
    echo "Image ${FMTFILE} creation complete."
    echo "Add the image to glance with the command:"
    GLANCECMD="sudo -E glance add name=${TDLNAME} is_public=true disk_format=${DISK_FORMAT} container_format=bare"
    echo "${GLANCECMD} < ${FMTFILE}"
else
    echo "Error creating image file ${FMTFILE}"
fi

rm -f ${LIBVIRT_XMLFILE}
