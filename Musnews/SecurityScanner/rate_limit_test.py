
import json
import secrets
import time
import urllib.error
import urllib.request

from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


BASE_URL = "http://localhost:5000"
LOGIN_PATH = "/api/Auth/login"

REQUEST_COUNT = 8
REQUEST_TIMEOUT = 8

SCANNER_DIR = Path(__file__).resolve().parent
REPORT_FILE = SCANNER_DIR / "rate_limit_report.json"


def check_rate_limiting(base_url: str = BASE_URL) -> dict:
    name = "Rate Limiting: защита от перебора паролей"

    result = {
        "name": name,
        "status": "ERROR",
        "description": "",
        "http_codes": []
    }

    parsed = urlparse(base_url)

    if (
        parsed.scheme not in ("http", "https")
        or parsed.hostname not in (
            "localhost",
            "127.0.0.1",
            "::1"
        )
    ):
        result["description"] = (
            "Разрешено тестирование только localhost."
        )
        print(f"\n[ERROR] {name}")
        print(result["description"])
        return result

    username = (
        "rate_limit_scanner_"
        + secrets.token_hex(8)
    )

    password = secrets.token_hex(24)

    payload = json.dumps({
        "username": username,
        "password": password
    }).encode("utf-8")

    url = base_url.rstrip("/") + LOGIN_PATH
    codes = []

    print("\n" + "-" * 45)
    print("ПРОВЕРКА RATE LIMITING")
    print("-" * 45)
    print("Отправляем 8 запросов с неверными данными.")

    started = time.monotonic()
    connection_error = None

    for number in range(1, REQUEST_COUNT + 1):
        request = urllib.request.Request(
            url=url,
            data=payload,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Musnews-Security-Scanner/1.2"
            }
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=REQUEST_TIMEOUT
            ) as response:
                status = response.status

        except urllib.error.HTTPError as error:
            status = error.code
            error.close()

        except (
            urllib.error.URLError,
            TimeoutError,
            OSError
        ) as error:
            connection_error = str(error)
            print(f"Попытка {number}: ошибка соединения")
            break

        codes.append(status)
        print(f"Попытка {number}: HTTP {status}")

        if status == 200:
            break

    elapsed = time.monotonic() - started

    result["http_codes"] = codes

    if connection_error:
        result["status"] = "ERROR"
        result["description"] = (
            "Проверка прервана из-за ошибки подключения: "
            + connection_error
        )

    elif 200 in codes:
        result["status"] = "FAIL"
        result["description"] = (
            "Сервер разрешил вход с заведомо "
            "неверными учётными данными. "
            "Требуется проверка авторизации."
        )

    elif any(code not in (401, 429) for code in codes):
        result["status"] = "WARNING"
        result["description"] = (
            "Получены неожиданные HTTP-коды: "
            + str(codes)
        )

    elif elapsed > 50:
        result["status"] = "WARNING"
        result["description"] = (
            "Проверка заняла слишком много времени. "
            "Запросы могли попасть в разные окна лимита."
        )

    elif (
        401 in codes
        and 429 in codes
        and codes.index(401) < codes.index(429)
    ):
        result["status"] = "PASS"
        result["description"] = (
            "Защита Rate Limiting сработала. "
            "После отклонённых попыток входа "
            "сервер начал возвращать HTTP 429."
        )

    elif codes and all(code == 429 for code in codes):
        result["status"] = "WARNING"
        result["description"] = (
            "Лимит был исчерпан до начала проверки. "
            "Повтори тест после сброса окна лимита "
            "или перезапуска тестового сервера."
        )

    elif (
        len(codes) == REQUEST_COUNT
        and all(code == 401 for code in codes)
    ):
        result["status"] = "FAIL"
        result["description"] = (
            "Все 8 попыток обработаны без HTTP 429. "
            "В данном тесте ограничение не сработало."
        )

    else:
        result["status"] = "WARNING"
        result["description"] = (
            "Результат неоднозначен. "
            f"Получены HTTP-коды: {codes}"
        )

    print(f"\n[{result['status']}] {name}")
    print(result["description"])

    return result


def main() -> None:
    result = check_rate_limiting()

    report = {
        "project": "Musnews",
        "module": "Rate Limiting",
        "created_at": (
            datetime.now()
            .astimezone()
            .isoformat(timespec="seconds")
        ),
        "target": BASE_URL,
        "check": result
    }

    try:
        with REPORT_FILE.open(
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                report,
                file,
                ensure_ascii=False,
                indent=4
            )

        print(f"\nОтчёт сохранён: {REPORT_FILE}")

    except OSError as error:
        print(f"Ошибка записи отчёта: {error}")


if __name__ == "__main__":
    main()
