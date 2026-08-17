# i didnt test anything lol 
import urllib.request
import urllib.error

GATEWAY_URL = "http://127.0.0.1:8080/test"
TOTAL_REQUESTS = 15


def SEND_REQUEST(url):
    try:
        response = urllib.request.urlopen(url)
        return response.status
    except urllib.error.HTTPError as e:
        return e.code


def main():
    results = []

    for i in range(TOTAL_REQUESTS):
        status = SEND_REQUEST(GATEWAY_URL)
        results.append(status)
        print(f"request {i + 1}: {status}")

    allowed = 0
    blocked = 0

    for i in range(len(results)):
        if results[i] == 200:
            allowed += 1
        elif results[i] == 429:
            blocked += 1

    print()
    print(f"allowed (200): {allowed}")
    print(f"blocked (429): {blocked}")


if __name__ == "__main__":
    main()

