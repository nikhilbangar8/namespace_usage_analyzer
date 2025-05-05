
## Get Current contexts
```sh
kubectl config get-contexts -o name
```
## Generate Report
```sh
python3 generate_report.py dev-staging kube-system 
```

## Run Server to View all reports
```sh
python3 -m http.server 8000
```

After this please open the next link : http://localhost:8000/report.html