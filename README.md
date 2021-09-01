# PyEGo

## Description
PyEGo: Inferring Environment Dependencies for Python Programs
## Introduction
PyEGo is a tool of automatically inferring environment dependencies for Python programs.<br/>
A Python program's environment dependencies mainly consists of three parts:
* Compatible Python interpreter version;
* Dependent Python third-party packages;
* Dependent System libraries.<br/>
For example, the following snippet print emoji on the terminal:
```python
import emoji
print emoji.emojize('Python is :thumbs_up:')
```
This snippet is only compatible with Python2, because there are no parentheses after "print".
If we run the snippet in Python3:
```$xslt
$ python example/example.py
File "example/example.py", line 2
  print emoji.emojize('Python is :thumbs_up:')
          ^
SyntaxError: invalid syntax
```
On the other hand, the snippet depends on a Python third-party package emoji. 
If we run the snippet without installing emoji:
```$xslt
$ python example.py 
Traceback (most recent call last):
  File "example/example.py", line 1, in <module>
    import emoji
ImportError: No module named emoji
```
PyEGo can build a runtime environment for the snippet:
```$xslt
$ python PyEGo.py -r example/example.py
```
And then, output a Dockerfile:
```dockerfile
FROM python:2.7
RUN apt-get clean
RUN apt-get update
RUN pip install --upgrade pip
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install emoji==0.6.0
ADD example.py example.py
# add CMD command to run your programs here
```
Add CMD instruction to run the snippet, build docker image:
```$xslt
$ echo "CMD python example.py" >> example/Dockerfile
$ cd example
$ docker build -t ego .
```
Now, run it!
```$xslt
$ docker run ego
Python is 👍
```
## Installation
### Install local
* Install Python>=3.6
* Install dependent Python packages:
```$xslt
$ pip install -r requirements.txt
```
* Install NEO4J>=3.5.13, <4
* Merge PyKG:
Our knowledge graph, PyKG, is split into 2 files because of file size limit, merge them before load it:
```$xslt
$ cat PyKG/PyKG.dump.a* >> PyKG.dump
```
* Load database(PyKG):
```$xslt
$ cp PyKG.dump /PATH/TO/NEO4J/data/databases/
$ cd /PATH/TO/NEO4J
$ bin/neo4j stop
$ bin/neo4j-admin load --from=data/databases/PyKG.dump
```
* Config PyEGo<br/>
Edit **config.py**, config neo4j connection:
```python
NEO4J_URI = "YOUR NEO4J URI"
NEO4J_PWD = "YOUR NEO4J PASSWORD"
```
### Docker
We also provide a Docker image of PyEGo. Build Docker image by:
```$xslt
$ docker build -t ego -f Docker/Dockerfile .
```

## Instructions
### Local
Start neo4j before running PyEGo:
```$xslt
$ cd /PATH/TO/NEO4J
$ bin/neo4j start
```
If you installed PyEGo local, you can use PyEGo by:
```$xslt
$ cd /PATH/TO/PyEGo
$ python PyEGo.py [-h] [-t OUTPUT_TYPE] [-p OUTPUT_PATH] -r PROGRAM_ROOT
             
```
* Program root can be either a single .py file or a Python project folder.<br/>
* PyEGo provides two types of output: Dockerfile, and dependency.json. Default output type is Dockerfile.<br/>
For a Dockerfile output, set --output_type=Dockerfile(-t Dockerfile), and for a json output, set --output_type=json.<br/>
* --output_path(-p) indicate the output path of the Dockerfile or dependency.json. PyEGo generates the file in the parent folder of PROGRAM_ROOT by default.
For more help, see:
```$xslt
$ python PyEGo.py -h
```

### Docker
If you built Docker image of PyEGo, you can use PyEGo by:
```$xslt
$ docker run -v /PATH/TO/PROGRAM/ROOT:/INPUT/IN/CONTAINER \
             -v /PATH/TO/OUTPUT:/OUTPUT/IN/CONTAINER \
             ego /INPUT/IN/CONTAINER /OUTPUT/IN/CONTAINER
```

## Replay our experiment
### Experiment on Hard-gists
Experimental results are available in another repository, [exp-gist](https://github.com/PyEGo/exp-gist).
#### Run PyEGo on Hard-gists
* Edit **experiment/exp_config.py**, config hard-gists root
```python
EGO_GISTS_ROOT = "/YOUR/HARD/GISTS/ROOT/OF/PYEGO"
```
* Run PyEGo
```$xslt
$ cd /PATH/TO/PYEGO
$ python experiment/tests_gist.py --run
```
#### Compare PyEGo results with DockerizeMe and Pipreqs
* Run DockerizeMe and Pipreqs<br/>
We provide our experiment bash script of DockerizeMe and Pipreqs<br/>
**script/dockerizeme_gen_df.sh** uses DockerizeMe to generate Dockerfiles for gists. Note that run the script in DockerizeMe vagrant(Provided by DockerizeMe)
```$xslt
# Run the script in DockerizeMe vagrant
# Edit line2: cd /YOUR/HARD/GISTS/ROOT/OF/DOCKERIZEME
$ cd /PATH/TO/PyEGo/script
$ bash dockerizeme_gen_df.sh
```
**script/pipreqs_gen_df.sh** uses Pipreqs to generate requirements.txt and Dockerfiles for gists. Note that run the script after install pipreqs(pip install pipreqs) in Python2.7
```$xslt
# Edit line2 and line3: /YOUR/HARD/GISTS/ROOT/OF/PIPREQS
$ cd /PATH/TO/PyEGo/script
$ bash pipreqs_gen_df.sh
```
**script/dockerize_all.sh** builds Docker images by DockerizeMe-generated or Pipreqs-generated Dockerfile, runs Docker containers, checks results and records results in log.txt.
```$xslt
# Edit line2: cd /YOUR/HARD/GISTS/ROOT
$ cd /PATH/TO/PyEGo/script
$ bash dockerize_all.sh
```
* Edit **experiment/exp_config.py**, config hard-gists root and log path
```python
EGO_GISTS_ROOT = "/YOUR/HARD/GISTS/ROOT/OF/PYEGO"
ME_GISTS_ROOT = "/YOUR/HARD/GISTS/ROOT/OF/DOCKERIZEME"
REQS_GISTS_ROOT = "/YOUR/HARD/GISTS/ROOT/OF/PIPREQS"

EGO_GISTS_LOG = "/YOUR/HARD/GISTS/LOG/PATH/OF/PYEGO"
ME_GISTS_LOG = "/YOUR/HARD/GISTS/LOG/PATH/OF/DOCKERIZEME"
REQS_GISTS_LOG = "/YOUR/HARD/GISTS/LOG/PATH/OF/PIPREQS"
```
* Compare results
```$xslt
$ cd /PATH/TO/PYEGO
$ python experiment/tests_gist.py --compare
```
### Experiment on Github dataset
Results of experiments are available in another repository, [exp-github](https://github.com/PyEGo/exp-github).
#### Download dataset
Our dataset is available on https://drive.google.com/file/d/1oHr6mbm0d5jIlVxeDkY6iyvow_Q63L_w/view.<br/>
* Unzip dataset:
```$xslt
$ tar -xvf GithubProjects.tar.gz
```
* Make copies for experiments:
```$xslt
$ cp GithubProjects /YOUR/GITHUB/DATASET/ROOT/OF/EGO
$ cp GithubProjects /YOUR/GITHUB/DATASET/ROOT/OF/PIPREQS
```
We need some copies of the dataset for our experiments. It's OK to use only one copy, but results would be overwriten.
#### Run PyEGo on Github dataset
* Edit **experiment/exp_config.py** github dataset root
```python
EGO_GITHUB_ROOT = "/YOUR/GITHUB/DATASET/ROOT/OF/EGO"
```
* Run PyEGo
```$xslt
$ cd /PATH/TO/PYEGO
$ python experiment/tests_github.py --run --tool=PyEGo
```

#### Compare PyEGo results with DockerizeMe and Pipreqs
* Run pipreqs<br/>
Install pipreqs in Python3.6+
Edit **experiment/exp_config.py**, config github dataset root and pipreqs path
```python
REQS_GITHUB_ROOT_39 = "/YOUR/GITHUB/DATASET/ROOT/OF/PIPREQS"
PIPREQS_PATH = "/YOUR/PIPREQS/PATH"
```
You can simply find pipreqs path by
```$xslt
$ which pipreqs
```
Run pipreqs
```$xslt
$ cd /PATH/TO/PYEGO
$ python experiment/tests_github.py --run --tool=Pipreqs
```
We provide results of DockerizeMe in [exp-github](https://github.com/PyEGo/exp-github).
* Edit **experiment/exp_config.py**, config github dataset root and log path
```python
EGO_GITHUB_ROOT = "/YOUR/GITHUB/DATASET/ROOT/OF/EGO"
REQS_GITHUB_ROOT_39 = "/YOUR/GITHUB/DATASET/ROOT/OF/PIPREQS"
ME_GITHUB_ROOT_39 = "/YOUR/GITHUB/DATASET/ROOT/OF/DOCKERIZEME"

EGO_GITHUB_LOG = "/YOUR/GITHUB/DATASET/LOG/PATH/OF/EGO"
REQS_GITHUB_LOG_39 = "/YOUR/GITHUB/DATASET/LOG/PATH/OF/PIPREQS"
ME_GITHUB_LOG_39 = "/YOUR/GITHUB/DATASET/LOG/PATH/OF/DOCKERIZEME"
```

* Compare results
```$xslt
$ cd /PATH/TO/PYEGO
$ python experiment/tests_github.py --compare
```
### Experiment running PyEGo with different strategies
Results of experiments are available in [exp-gist](https://github.com/PyEGo/exp-gist).
* Here are our 2 strategies:<br/>

|id|select strategy|
|----|-----|
|1(default)|select-one|
|2|select-all|

* Edit **experiment/exp_config.py**, config hard-gist root
```python
EGO_GISTS_ROOT = "/YOUR/HARD/GIST/DATASET/ROOT/OF/PYEGO/STRATEGY1"
EGO_GISTS_ROOT_2 ="/YOUR/HARD/GIST/DATASET/ROOT/OF/PYEGO/STRATEGY2"
```
* Run strategy<X> on Hard-gists:
```$xslt
$ cd /PATH/TO/PYEGO
$ python experiment/tests_strategies.py --strategy=X
```
