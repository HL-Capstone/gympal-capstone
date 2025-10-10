import time, statistics, requests

URL = "http://127.0.0.1:5000/api/metrics/Squat"
N = 50

def main():
    lat = []
    for _ in range(N):
        t0 = time.perf_counter()
        r = requests.get(URL, timeout=5)
        r.raise_for_status()
        lat.append((time.perf_counter() - t0) * 1000.0)
    p95 = sorted(lat)[int(0.95*len(lat))-1]
    print(f"n={N}, avg_ms={statistics.mean(lat):.2f}, p50_ms={statistics.median(lat):.2f}, p95_ms={p95:.2f}")

if __name__ == "__main__":
    main()
