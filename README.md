# Website Tester
Website tester based on Python.

## Quick start
Console
```
pyhon test_website.py --url http://example.com/ --rps 100 --duration 5 --timeout 10
```

Configuration file
```
pyhon test_website.py --config config.json
```

## Example of analysis results
```
Target URL: https://www.bitrix24.ru/prices/
Test duration: 5s, RPS: 100 (total 500 requests)
Timeout for responses: 10s

<=== Request Summary ===>
Total:		500
Success:	277
Failure:	223
- HTTP errors:		223

<=== Response Time (s) ===>
Min:	2.902
Max:	11.208
Mean:	7.923
Median:	8.305
p75:	10.439
p90:	10.973
p95:	11.071
p99:	11.165

<=== Status Code Distribution ===>
http (1xx):	0
http (2xx):	277
http (3xx):	0
http (4xx):	0
http (5xx):	223
Details:
- 200:	277	(OK)
- 503:	223	(Service Temporarily Unavailable)

<=== Network Parameters ===>
Download size:	3.608 Mb
Download speed:	0.455 Mb/s
Redirects count:	0
Cached responses:	0
```
