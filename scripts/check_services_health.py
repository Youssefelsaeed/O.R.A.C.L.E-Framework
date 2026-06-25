import json

import requests


SERVICES = {
    "qauth": "http://localhost:8001/health",
    "chrono": "http://localhost:8003/health",
    "ethicq": "http://localhost:8004/health",
}


def check_services_health():
    result = {}
    for name, url in SERVICES.items():
        try:
            response = requests.get(url, timeout=2)
            result[name] = response.status_code < 400
        except Exception:
            result[name] = False
    return result


def main():
    print(json.dumps(check_services_health(), indent=2))


if __name__ == "__main__":
    main()

