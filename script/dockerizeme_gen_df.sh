#! /bin/bash
cd /YOUR/HARD/GISTS/ROOT/FOR/DOCKERIZEME
date >> ../DockerizeMe.log
for folder in `ls .`
do
	echo $folder	
	cd $folder
	dockerizeme --verbose > Dockerfile
	cd ..
done
date >> ../DockerizeMe.log
