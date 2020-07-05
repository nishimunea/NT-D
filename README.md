# NT-D (Network Threat Detector)



## Local Debug

Install and run [Minikube](https://kubernetes.io/ja/docs/tasks/tools/install-minikube/) on your computer and create a database pod as follows.

```
kubectl run --generator=run-pod/v1 --image=mysql:5.7 ntd-database --port=3306 --env="MYSQL_DATABASE=ntd" --env="MYSQL_ROOT_PASSWORD=password" -- --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci
kubectl port-forward ntd-database 3306:3306
```

Run following commands in `core/` directory.

```
pipenv install -d
pipenv run server
pipenv run cron
```

Run following commands in `ui/` directory.

```
npm ci
npm run serve
```

Visit `http://localhost:8080/` on your browser and use `password` for the administrator login.


## Disclaimer

We impose restrictions on your use of this tool. You are prohibited from attempting to interfere with any networks or hosts you are not authorized to access. You must first secure written authorization from owner of your target before initiating any scanning. It is to be understood that we shall not be held responsible for any damage incurred as a result of scanning by this tool.