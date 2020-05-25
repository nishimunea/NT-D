# NT-D (Network Threat Detector)



## Local Debug

* Install and start [Minikube](https://kubernetes.io/ja/docs/tasks/tools/install-minikube/) on your computer.

* Run following commands in `core` directory.

```
docker run -e MYSQL_DATABASE=ntd -e MYSQL_ROOT_PASSWORD=Passw0rd! -d -p 3306:3306 mysql:5.7 --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci
pipenv install -d
pipenv run server
pipenv run cron
```

* Run following commands in `ui` directory.

```
npm ci
npm run serve
```

* Visit `http://localhost:8080/` on your browser.

* Use `password` for the administrator login.

## Disclaimer

We impose restrictions on your use of this tool. You are prohibited from attempting to interfere with any networks or hosts you are not authorized to access. You must first secure written authorization from owner of your target before initiating any scanning. It is to be understood that we shall not be held responsible for any damage incurred as a result of scanning by this tool.