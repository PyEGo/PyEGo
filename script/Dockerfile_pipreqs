FROM python:2.7
RUN pip install --upgrade pip
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt
ADD snippet.py snippet.py
# add CMD command to run your programs here
CMD python snippet.py
