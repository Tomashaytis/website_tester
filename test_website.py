import json
import argparse
from website_tester import WebsiteTester

if __name__ == '__main__':
    params = {}
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', type=str, default=None, help='path to config file')
    parser.add_argument('-u', '--url', type=str, default=None, help='URL')
    parser.add_argument('-r', '--rps', type=int, default=5, help='test RPS')
    parser.add_argument('-d', '--duration', type=int, default=5, help='test duration (s)')
    parser.add_argument('-t', '--timeout', type=int, default=5, help='timeout for responses (s)')
    args = parser.parse_args()

    if args.config is not None:
        try:
            with open(args.config, 'r', encoding='utf-8') as fp:
                params = json.load(fp)
        except OSError as err:
            print(f'Error opening file: {err}')
            exit(1)
        except json.JSONDecodeError as err:
            print(f'Error parsing file: {err}')
            exit(1)
    else:
        if args.url is None:
            print('URL not specified')
            exit(1)
        params['url'] = args.url
        params['rps'] = args.rps
        params['duration'] = args.duration
        params['timeout'] = args.timeout
        params['payload'] = ""

    tester = WebsiteTester(params['url'], params['rps'], params['duration'], params['timeout'], params['payload'])
    tester.start_testing()
