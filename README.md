## [Бейджик об удачно завершенном workflow](https://github.com/IvanPrudey/foodgram/actions/workflows/main.yml/badge.svg)

## О проекте foodgram:
«Фудграм» — сайт, на котором пользователи могут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированным пользователям также будет доступен сервис «Список покупок». Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд.
Для проекта секреты подключаются из файла .env, также из Repository secrets на github.com.
С помощью GitHub Actions через workflof реализована автоматизация: 
* проверки кода бэкенда на PEP8
* сборки образов и отправки их на Docker Hub
* обновления на сервере и перезапуска приложения при помощи Docker Compose
* выполнения команды для сборки статики в приложении бэкенда 
* переноса статики в volume, выполнения миграции
* информирования сообщением в TG об успешном деплое .

## Cтек использованных технологий:
```
Python
Django
djangorestframework
gunicorn
nginx
postgresql
GitHub Actions
```

## Как запустить проект: 
Клонировать репозиторий и перейти в него в командной строке: 
``` 
git clone https://github.com/IvanPrudey/foodgram.git 
``` 
``` 
cd foodgram/backend
``` 

Cоздать и активировать виртуальное окружение: 
``` 
python -m venv venv 
``` 
``` 
source venv/Scripts/activate 
``` 
``` 
python -m pip install --upgrade pip 
``` 

Установить зависимости из файла requirements.txt: 
``` 
pip install -r requirements.txt 
```

Перейти в директорию с файлом manage.py: 
```
/backend/foodgram
```

Создать и применить миграции: 
```
python manage.py makemigrations
python manage.py migrate

```

Загрузить данные ингредиентов из файла CSV с помощью скрипта: 
```
python manage.py load_data_script
```

Создать суперпользователя: 
```
python manage.py createsuperuser
```
-------------

Установить значения констант для доступа к БД в файле .env
```
POSTGRES_DB=<имя базы данных>
POSTGRES_USER=<имя пользователя>
POSTGRES_PASSWORD=<пароль пользователя>
DB_HOST=<хост или имя контейнера, где запущен сервер БД> 
DB_PORT=<порт, по которому Django будет обращаться к базе данных. 5432 — это порт по умолчанию для PostgreSQL>
SECRET_KEY=<для файла конфигурации settings.py>
DEBUG=<режим локальной отладки>
ALLOWED_HOSTS=<список имен хостов/доменов, на которых может обслуживаться ваш веб-сервер>
TESTING_WITH_SQLITE3=<режим переключения на базу SQLITE3 для отладки на локальной машине>
```

# Сохранить значения констант в секретах GitHub Actions:

* для доступа к серверу:
```
SSH_KEY <SSH-ключ>
USER <имя пользователя>
SSH_PASSPHRASE <passphrase в паре к ssh ключу>
HOST <адрес хоста>
```

* для аутентификации в Docker Hub:
```
DOCKER_USERNAME <логин>
DOCKER_PASSWORD <пароль>
```

* для реализации отправки сообщения в TG:
```
TELEGRAM_TO <ID своего телеграм-аккаунта>
TELEGRAM_TOKEN <токен вашего бота>
```

## с подробной спецификацией API можно ознакомиться по адресу:
```
http://localhost/api/docs/
```

## Автор работы - ученик когорты 97 ЯндексПрактикум, курса Python-разработчик:
* Прудий Иван