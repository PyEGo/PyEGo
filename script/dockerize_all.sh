#! /bin/bash
cd /YOUR/HARD/GISTS/ROOT
date >> ../log.txt
#i=0
for folder in `ls .`
do
	dockerized=`cat ../log.txt |grep $folder`
	if [ "$dockerized"x != ""x ];
	then
		#i=$[$i+1];
		echo $folder dockerized
		continue
	fi
	#echo dockerized $i files
	echo $folder
	cd $folder
	#dockerizeme --verbose > Dockerfile
	docker build -t ptme -f ./Dockerfile .
	img=`docker images |grep ptme`
	if [ "$img"x = ""x ];
	then
		echo $folder failed >> ../../log.txt
		cd ..
		continue
	fi
	docker run --name me -d ptme
	sleep 5
	docker logs me >& log.txt
	docker stop me
	docker rm me
	import_error=`cat log.txt |grep ImportError`
	if [ "$import_error"x != ""x ];
	then
		echo $folder failed >> ../../log.txt
	else
		echo $folder success >> ../../log.txt
	fi
	docker rmi ptme -f
	cd ..
done
date >> ../log.txt
