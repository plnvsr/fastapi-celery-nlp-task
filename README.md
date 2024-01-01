docker-compose build 
docker-compose up 

then curl localhost:8000/scrape to scrape data. 

this will write corp_data.json on your local directory. 

python group.py to group the data.
