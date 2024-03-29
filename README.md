# Yatube

### Описание проекта:

Учебный проект. Мини социальная сеть для публикации постов, с возможностью размещения картинок, комментариев к постам и подписки на авторов.
Реализован на фреймворке Django и встроенной в него БД sqlite с применением шаблонов html. Реализована раздача статики. 


### Системные требования: 

python 3.7


### Инструкция по развёртыванию:

Создать виртуальное окружение:
```
python -m venv venv
```

Запустить виртуальное окружение:
```
source venv/Scripts/activate
```

Установить используемые библиотеки:
```
pip install -r requirements.txt
```

Создать миграции для моделей БД:
```
python yatube/manage.py makemigrations
```

Применить миграции:
```
python yatube/manage.py migrate
```

Создать суперпользователя для администрирования:
```
python yatube/manage.py createsuperuser
```

Запустить веб-сервер:
```
python yatube/manage.py runserver
```


![example workflow](https://github.com/jd60-perm/hw05_final/actions/workflows/main.yml/badge.svg)