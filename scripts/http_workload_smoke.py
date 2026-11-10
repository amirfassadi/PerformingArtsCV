import argparse
import concurrent.futures
import statistics
import time
from urllib.request import Request, urlopen


def fetch(url):
    started = time.perf_counter()
    try:
        with urlopen(Request(url, method='GET'), timeout=10) as response:
            response.read()
            return response.status, time.perf_counter() - started
    except Exception as error:
        return error.__class__.__name__, time.perf_counter() - started


def main():
    parser = argparse.ArgumentParser(description='Bounded local HTTP workload smoke test.')
    parser.add_argument('--url', required=True)
    parser.add_argument('--requests', type=int, default=40)
    parser.add_argument('--concurrency', type=int, default=4)
    options = parser.parse_args()
    if not 1 <= options.requests <= 500 or not 1 <= options.concurrency <= 20:
        raise SystemExit('requests must be 1..500 and concurrency must be 1..20')
    started = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=options.concurrency) as pool:
        results = list(pool.map(fetch, [options.url] * options.requests))
    elapsed = time.perf_counter() - started
    failures = [result for result in results if result[0] != 200]
    latencies = [result[1] for result in results]
    print(
        f'url={options.url} requests={options.requests} concurrency={options.concurrency} '
        f'elapsed={elapsed:.3f}s failures={len(failures)} '
        f'p50={statistics.median(latencies):.4f}s max={max(latencies):.4f}s',
    )
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
