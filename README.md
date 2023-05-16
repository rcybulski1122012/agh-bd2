# System zarządzania biblioteką

## Skład Grupy
- Radosław Cybulski rcybulski@student.agh.edu.pl
- Jakub Chrzanowski jchrzanowski@student.agh.edu.pl

## Technologie
- Python
- MongoDB
- Flask


## Uruchamianie
- Utwórz i aktywuj wirtualne środowisko
    ```bash
    python -m venv venv
    source venv/bin/activate  # na systemie Linux lub MacOS
    venv\Scripts\activate     # na systemie Windows
    ```
- Zainstaluj potrzebne pakiety 
    ```bash 
    pip install -r requirements.txt
    ```
- Ustaw zmienną środowiskową `MONGO_URI`  
- Uruchom serwer aplikacji
    ```bash
    python -m app 
    ```
  

## Przydatne linki
- [Dokumentacja Flask](https://flask.palletsprojects.com/en/2.3.x/)
- [Dokumentacja Flask-PyMongo](https://flask-pymongo.readthedocs.io/en/latest/)
- [Dokumentacja Flask-Login](https://flask-login.readthedocs.io/en/latest/)
- [Dokumentacja Jinja](https://jinja.palletsprojects.com/en/3.1.x/)
