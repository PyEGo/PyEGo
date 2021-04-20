FROM python:3.9
# install java and neo4j
RUN apt-get update && apt-get install default-jre -y
RUN wget http://doc.we-yun.com:1008/neo4j/3.5.26/neo4j-community-3.5.26-unix.tar.gz && tar -xvf neo4j-community-3.5.26-unix.tar.gz  && mv neo4j-community-3.5.26 neo4j
# config neo4j
RUN echo "dbms.connectors.default_listen_address=0.0.0.0" >> /neo4j/conf/neo4j.conf && echo "dbms.security.auth_enabled=false" >> /neo4j/conf/neo4j.conf
# install py deps
RUN pip install z3-solver>=4.8.9.0 typed-ast>=1.4.1 tqdm>=4.54.1 py2neo>=4.3.0 docker>=4.4.0 compare-string-version==0.1.0
# load PyKG
ADD . /PyEGo
RUN cat PyKG/PyKG.dumpa* >> PyKG.dump
RUN /neo4j/bin/neo4j-admin load --from=/PyEGo/PyKG.dump
# config PyEGo-neo4j connection
RUN echo "NEO4J_PWD = None" >> /PyEGo/config.py
ENTRYPOINT ["/bin/bash", "/PyEGo/Docker/ego.sh"]
CMD ["/PyEGo/example/example.py", "/PyEGo/example/"]
