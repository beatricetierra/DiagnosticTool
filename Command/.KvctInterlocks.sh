#!/bin/sh

# Make directory 
if [[ ! -d "/home/rxm/$1" ]]
then
        echo "Directory doesn't exist. Creating now"
        mkdir /home/rxm/$1
        echo "Directory created"
else	
       	echo "Directory already exists. Adding files to directory"
	rm -r /home/rxm/$1
	mkdir /home/rxm/$1
fi

# Get all log files with chosen date
d=
n=0
until [ "$d" = "$3" ]
do  
	d=$(date -d "$2 + $n days" "+%Y-%m-%d")
	cp -r /home/rxm/log/archive/$d/*-pet_recon-* /home/rxm/$1
	scp -r 192.168.10.106:/home/rxm/log/archive/$d/*-kvct-* /home/rxm/$1
	scp -r 192.168.10.110:/home/rxm/log/archive/$d/*-sysnode-* /home/rxm/$1
	((n++))
done

echo "Finding Interlocks"
python3 ./kvct/GetKvctInterlocks.py /home/rxm/$1 $2 $3
