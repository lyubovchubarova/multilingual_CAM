# multilingual_CAM
This repo contains an application for multilingual Comparative Argumentation Machine with a multilingual bias removal tool and additional materials used to build this application and reflected the process of research.

The app hosted at http://82.148.28.55/

`App` folder contains the application itself

`Medium-data-scraping` folder contains a tool to parse a medium website by thematical tags without limitations by number of requests, articles and paywall limitation

`Models` (to be updated) contain the jupyter notebooks where different comparative sentences classifier were learnt

## How to launch the app

The online version is availiable at http://82.148.28.55/, however, if you want to run it locally do the next

1. Ensure that you have Docker on your computer
2. Pull the latest version of dokerized elastic search from Docker Hub
3. Run this command on terminal to laund an elastic search server
```
docker run --rm -p 9200:9200 -p 9300:9300 -e "xpack.security.enabled=false" -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch
```
5.  Clone the repo and run `app.py`
6.  The app will be running at http://localhost:5000


