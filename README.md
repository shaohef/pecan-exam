# pecan-exam
An simple example that use pecan to create a restful server

## install and start

`git clone https://github.com/shaohef/pecan-exam.git`

`pip install pecan`

`cd pecan-exam`

`sudo python setup.py develop`

`pecan serve config.py`

## Test the server with this command, it will return success.


```
curl -i -X POST http://localhost:6060/ips \
-H 'Content-Type: application/json' -H "Accept: application/json" -d '
{"systemips":  
  {  
    "host": "127.0.0.1",  
    "edge": "127.0.0.2",  
    "sip": "127.0.0.3",  
    "mcu": "127.0.0.4"  
}}'
```

It will return as follow:

```
HTTP/1.0 201 Created
Date: Mon, 20 Aug 2018 00:49:53 GMT
Server: WSGIServer/0.1 Python/2.7.12
Content-Length: 29
Content-Type: application/json

{"status": "POST SUCCESS!\n"}
```

## Test the server with this command, it will return error.

>curl -i -X POST http://localhost:6060/ips \  
>-H 'Content-Type: application/json' -H "Accept: application/json" -d '  
>{"systemips":  
>  {  
>    "host": "127.0.0.1",  
>    "edge": "127.0.0.2",  
>    "sip": "127.0.0.3",  
>    "bad": "127.0.0.4"  
>}}'


It will return as follow:

```
HTTP/1.0 400 Bad Request
Date: Mon, 20 Aug 2018 00:49:25 GMT
Server: WSGIServer/0.1 Python/2.7.12
Content-Length: 53
Content-Type: application/json

{"message": "Missing these ips in the context: mcu."}
```

response status is **400**, missing **mcu** ip setting.
