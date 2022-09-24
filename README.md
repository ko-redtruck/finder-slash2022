# finder-slash2022

Installation
1. Install requirements
```
pip install websockets tmdbv3api watchdog[watchmedo]
```
2. Add the movie databse api key 
```
export TMDB_API_KEY='YOUR_API_KEY'
```
3. Start app without code reloading or with
``` 
python app.py
```

```
watchmedo auto-restart --pattern "*.py" --recursive --signal SIGTERM \
    python app.py
```
