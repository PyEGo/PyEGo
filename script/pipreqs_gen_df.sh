#! /bin/bash
cp Dockerfile_pipreqs /YOUR/HARD/GISTS/ROOT/FOR/PIPREQS/..
cd /YOUR/HARD/GISTS/ROOT/FOR/PIPREQS
date >> ../Pipreqs.log
for folder in `ls .`
do
	cd $folder
	pipreqs . --force
	cp ../../Dockerfile_pipreqs Dockerfile
	cd ..
done
date >> ../Pipreqs.log
