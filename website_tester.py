from typing import List
import asyncio
import requests

class WebsiteTester:
    def __init__(self, url, rps = 1, duration = 1, payload = ""):
        self._url = url
        self._rps = rps
        self._duration = duration
        self._payload = payload
        self._test_results = {}
        self.init_test_results()

    def init_test_results(self):
        self._test_results = {
            'total': self._rps * self._duration,
            'timestamps': {
                'start': None,
                'end': None,
                'duration': 0,
            },
            'success': 0,
            'failure': {
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
                    '>2s': 0,
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
            'load': {
                'rps_achieved': 0,
                'concurrency': 0,
                'throughput': 0,
            },
            'network': {
                'dns_time': 0,
                'connect_time': 0,
                'ttfb': 0,
                'download_speed': 0,
                'upload_size': 0,
                'download_size': 0,
            },
            'misc': {
                'retries': 0,
                'redirects': 0,
                'cached': 0,
            }
        }

    async def send_test_request(self) -> requests.Response:
        return requests.get(self._url, params=self._payload)

    def analyze_responses(self, responses: List[requests.Response]):
        pass

    async def send_test_requests(self) -> List[requests.Response]:
        responses = []
        for i in range(self._duration):
            tasks = []
            for j in range(self._rps):
                tasks.append(self.send_test_request())

            responses.extend(await asyncio.gather(*tasks))
            await asyncio.sleep(1)
        return responses

