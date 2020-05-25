# NT-D (Network Threat Detector)



## Local Debug

First, install and start [Minikube](https://kubernetes.io/ja/docs/tasks/tools/install-minikube/) on your computer.

Move to the `core` directory, run following commands.

```
docker run -e MYSQL_DATABASE=ntd -e MYSQL_ROOT_PASSWORD=Passw0rd! -d -p 3306:3306 mysql:5.7 --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci
pipenv install -d
pipenv run server
pipenv run cron
```

Move to the `ui` directory, run following commands.

```
npm ci
npm run serve
```

Visit `http://localhost:8080/` on your browser.

Use `password` in the administrator login form.
