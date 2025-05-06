import asyncio
import httpx
import statistics
from tqdm import tqdm
from tqdm.asyncio import tqdm_asyncio
from typing import List, Tuple, Optional
from datetime import datetime

class WebsiteTester:
    def __init__(self, url: str, rps: int = 1, duration: int = 1, timeout: int = 10, payload = ""):
        self._url = url
        self._rps = rps
        self._duration = duration
        self._payload = payload
        self._timeout = timeout
        self._metrics = {}
        self.init_metrics()

    def init_metrics(self):
        self._metrics = {
            'total': self._rps * self._duration,
            'timestamps': {
                'start': None,
                'end': None,
                'duration': 0,
            },
            'success': 0,
            'failure': {
                'all': 0,
                'timeout': 0,
                'connection': 0,
                'http': 0,
                'ssl': 0,
                'redirects': 0,
                'other': 0,
            },
            'time': {
                'min': 0,
                'max': 0,
                'mean': 0,
                'median': 0,
                'p75': 0,
                'p90': 0,
                'p95': 0,
                'p99': 0,
                'histogram': {
                    '0-100ms': 0,
                    '100-300ms': 0,
                    '300-500ms': 0,
                    '500-1000ms': 0,
                    '1-2s': 0,
                    '2-?s': 0,
                }
            },
            'status': {
                'codes': {},
                '1xx': 0,
                '2xx': 0,
                '3xx': 0,
                '4xx': 0,
                '5xx': 0,
            },
            'network': {
                'download_speed': 0,
                'download_size': 0,
                'redirects': 0,
                'cached': 0,
            }
        }

    async def send_test_request(self, client: httpx.AsyncClient) -> Tuple[Optional[httpx.Response], float]:
        response = None
        start = datetime.now()
        try:
            response = await client.get(self._url, params=self._payload, follow_redirects=True)
        except httpx.TimeoutException:
            self._metrics['failure']['timeout'] += 1
            self._metrics['failure']['all'] += 1
            return response, self._timeout
        except httpx.ConnectError as err:
            if "SSL" in str(err):
                self._metrics['failure']['ssl'] += 1
            else:
                self._metrics['failure']['connection'] += 1
            self._metrics['failure']['all'] += 1
        except httpx.RemoteProtocolError:
            self._metrics['failure']['redirects'] += 1
            self._metrics['failure']['all'] += 1
        except httpx.RequestError as e:
            self._metrics['failure']['other'] += 1
            self._metrics['failure']['all'] += 1
        end = datetime.now()
        time_delta = end - start
        return response, time_delta.total_seconds()

    def analyze_responses(self, responses: List[Tuple[Optional[httpx.Response], float]]):
        download_sizes = []
        times = []
        for response, time in responses:
            times.append(time)
            if response is None:
                continue
            if time < 0.1:
                self._metrics['time']['histogram']['0-100ms'] += 1
            elif time < 0.3:
                self._metrics['time']['histogram']['100-300ms'] += 1
            elif time < 0.5:
                self._metrics['time']['histogram']['300-500ms'] += 1
            elif time < 1:
                self._metrics['time']['histogram']['500-1000ms'] += 1
            elif time < 2:
                self._metrics['time']['histogram']['1-2s'] += 1
            else:
                self._metrics['time']['histogram']['2-?s'] += 1

            download_sizes.append(len(response.content))
            self._metrics['network']['redirects'] = len(response.history)
            if 'from-cache' in response.headers.get('X-Cache', '').lower():
                self._metrics['misc']['cached'] += 1

            self._metrics['success'] += response.is_success
            self._metrics['failure']['http'] += response.is_error
            self._metrics['failure']['all'] += response.is_error
            if 100 <= response.status_code < 200:
                self._metrics['status']['1xx'] += 1
            if 200 <= response.status_code < 300:
                self._metrics['status']['2xx'] += 1
            if 300 <= response.status_code < 400:
                self._metrics['status']['3xx'] += 1
            if 400 <= response.status_code < 500:
                self._metrics['status']['4xx'] += 1
            if 500 <= response.status_code < 600:
                self._metrics['status']['5xx'] += 1
            if response.status_code in self._metrics['status']['codes']:
                self._metrics['status']['codes'][response.status_code]['count'] += 1
            else:
                self._metrics['status']['codes'][response.status_code] = {'paraphrase': response.reason_phrase, 'count': 1}

        self._metrics['time']['min'] = min(times)
        self._metrics['time']['max'] = max(times)
        self._metrics['time']['mean'] = statistics.mean(times)
        self._metrics['time']['median'] = statistics.median(times)
        quantile = statistics.quantiles(times, n=100)
        self._metrics['time']['p75'] = quantile[74]
        self._metrics['time']['p90'] = quantile[89]
        self._metrics['time']['p95'] = quantile[94]
        self._metrics['time']['p99'] = quantile[98]


        download_time = statistics.mean(times)
        download_size = int(statistics.mean(download_sizes)) / 1024 / 1024 if len(download_sizes) != 0  else 0
        self._metrics['network']['download_size'] = download_size
        self._metrics['network']['download_speed'] = download_size / download_time

        self._metrics['status']['codes'] = dict(sorted(self._metrics['status']['codes'].items()))

    async def send_test_requests(self) -> List[Tuple[Optional[httpx.Response], float]]:
        self._metrics['timestamps']['start'] = datetime.now()
        timeout = httpx.Timeout(self._timeout)

        async with httpx.AsyncClient(timeout=timeout) as client:
            tasks = []
            for _ in tqdm(range(self._duration), desc='Requesting'):
                start = datetime.now()
                for i in range(self._rps):
                    tasks.append(self.send_test_request(client))
                    time_delta = datetime.now() - start
                    if time_delta.total_seconds() < i / self._rps:
                        await asyncio.sleep(i / self._rps - time_delta.total_seconds())
            responses = await tqdm_asyncio.gather(*tasks, desc='Receiving')

        self._metrics['timestamps']['end'] = datetime.now()
        time_delta = self._metrics['timestamps']['end'] - self._metrics['timestamps']['start']
        self._metrics['timestamps']['duration'] = time_delta.total_seconds()

        return responses

    def start_testing(self):
        self.init_metrics()
        responses = asyncio.run(self.send_test_requests())
        self.analyze_responses(responses)
        print()
        self.print_metrics()

    def print_metrics(self):
        print(f'Target URL: {self._url}')
        print(f'Test duration: {self._duration}s, RPS: {self._rps} (total {self._metrics['total']} requests)')
        print(f'Timeout for responses: {self._timeout}s')
        print()

        print('<=== Request Summary ===>')
        print(f'Total:\t\t{self._metrics['total']}')
        print(f'Success:\t{self._metrics['success']}')
        print(f'Failure:\t{self._metrics['failure']['all']}')
        if self._metrics['failure']['timeout'] != 0:
            print(f'- Timeout errors:\t{self._metrics['failure']['timeout']}')
        if self._metrics['failure']['connection'] != 0:
            print(f'- Connection errors:\t{self._metrics['failure']['connection']}')
        if self._metrics['failure']['http'] != 0:
            print(f'- HTTP errors:\t\t{self._metrics['failure']['http']}')
        if self._metrics['failure']['ssl'] != 0:
            print(f'- SSL errors:\t\t{self._metrics['failure']['ssl']}')
        if self._metrics['failure']['redirects'] != 0:
            print(f'- Redirect errors:\t{self._metrics['failure']['redirects']}')
        if self._metrics['failure']['other'] != 0:
            print(f'- Other errors:\t\t{self._metrics['failure']['other']}')
        print()

        print('<=== Response Time (s) ===>')
        print(f'Min:\t{self._metrics['time']['min']:.3f}')
        print(f'Max:\t{self._metrics['time']['max']:.3f}')
        print(f'Mean:\t{self._metrics['time']['mean']:.3f}')
        print(f'Median:\t{self._metrics['time']['median']:.3f}')
        print(f'p75:\t{self._metrics['time']['p75']:.3f}')
        print(f'p90:\t{self._metrics['time']['p90']:.3f}')
        print(f'p95:\t{self._metrics['time']['p95']:.3f}')
        print(f'p99:\t{self._metrics['time']['p99']:.3f}')
        print()

        print('<=== Status Code Distribution ===>')
        print(f'http (1xx):\t{self._metrics['status']['1xx']}')
        print(f'http (2xx):\t{self._metrics['status']['2xx']}')
        print(f'http (3xx):\t{self._metrics['status']['3xx']}')
        print(f'http (4xx):\t{self._metrics['status']['4xx']}')
        print(f'http (5xx):\t{self._metrics['status']['5xx']}')
        print('Details:')
        for code in self._metrics['status']['codes']:
            print(f'- {code}:\t{self._metrics['status']['codes'][code]['count']}\t'
                  f'({self._metrics['status']['codes'][code]['paraphrase']})')
        print()

        print('<=== Network Parameters ===>')
        print(f'Download size:\t{self._metrics['network']['download_size']:.3f} Mb')
        print(f'Download speed:\t{self._metrics['network']['download_speed']:.3f} Mb/s')
        print(f'Redirects count:\t{self._metrics['network']['redirects']}')
        print(f'Cached responses:\t{self._metrics['network']['cached']}')


