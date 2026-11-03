
import json
import re
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from xss_browser_test import check_xss


# Адрес запущенного Musnews
BASE_URL = "http://localhost:5000"

# Пути к файлам проекта
SCANNER_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCANNER_DIR.parent

INDEX_FILE = (
    PROJECT_DIR
    / "Musnews.Server"
    / "wwwroot"
    / "index.html"
)

REPORT_FILE = SCANNER_DIR / "report.json"

results = []


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self, request, fp, code, msg, headers, newurl
    ):
        return None


def add_result(name, status, description):
    result = {
        "name": name,
        "status": status,
        "description": description
    }

    results.append(result)

    print(f"\n[{status}] {name}")
    print(description)


def request_status(path):
    url = BASE_URL.rstrip("/") + path

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Musnews-Security-Scanner/1.0"
        },
        method="GET"
    )

    opener = urllib.request.build_opener(NoRedirect())

    try:
        with opener.open(request, timeout=5) as response:
            return response.status, None

    except urllib.error.HTTPError as error:
        return error.code, None

    except (urllib.error.URLError, TimeoutError, OSError) as error:
        return None, str(error)


def check_server():
    status, error = request_status("/index.html")

    if error:
        add_result(
            "Подключение к Musnews",
            "ERROR",
            f"Сервер недоступен: {error}"
        )
        return False

    if status == 200:
        add_result(
            "Подключение к Musnews",
            "PASS",
            "Сайт доступен. HTTP 200."
        )
        return True

    add_result(
        "Подключение к Musnews",
        "WARNING",
        f"Сервер ответил HTTP {status}."
    )

    return False


def check_tracks_access():
    status, error = request_status("/api/tracks")

    if error:
        add_result(
            "Доступ к трекам без авторизации",
            "ERROR",
            error
        )
        return

    if status in (401, 403):
        add_result(
            "Доступ к трекам без авторизации",
            "PASS",
            f"Доступ ограничен. HTTP {status}."
        )

    elif status == 200:
        add_result(
            "Доступ к трекам без авторизации",
            "FAIL",
            "API возвращает HTTP 200 без авторизации. "
            "Необходимо проверить, доступны ли чужие данные."
        )

    else:
        add_result(
            "Доступ к трекам без авторизации",
            "WARNING",
            f"Неожиданный ответ HTTP {status}."
        )


def check_playlists_access():
    status, error = request_status("/api/playlists")

    if error:
        add_result(
            "Доступ к общим плейлистам",
            "ERROR",
            error
        )
        return

    if status == 200:
        add_result(
            "Доступ к общим плейлистам",
            "INFO",
            "Список плейлистов доступен без авторизации. "
            "Нужно проверить, предусмотрено ли это "
            "требованиями приложения."
        )

    elif status in (401, 403):
        add_result(
            "Доступ к общим плейлистам",
            "PASS",
            f"Доступ ограничен. HTTP {status}."
        )

    else:
        add_result(
            "Доступ к общим плейлистам",
            "WARNING",
            f"Ответ сервера: HTTP {status}."
        )


def check_xss_source():
    if not INDEX_FILE.is_file():
        add_result(
            "Статическая проверка XSS",
            "ERROR",
            f"Не найден файл: {INDEX_FILE}"
        )
        return

    try:
        source = INDEX_FILE.read_text(
            encoding="utf-8-sig"
        )

    except (OSError, UnicodeError) as error:
        add_result(
            "Статическая проверка XSS",
            "ERROR",
            str(error)
        )
        return

    vulnerable_pattern = (
        r"<div>\s*\$\{\s*playlist\.name\s*\}\s*</div>"
    )

    safe_pattern = (
        r"""querySelector\(\s*['"]#safePlaylistTitle['"]\s*\)"""
        r"\s*\.textContent\s*=\s*playlist\.name"
    )

    vulnerable = bool(
        re.search(vulnerable_pattern, source)
    )

    protected = (
        'id="safePlaylistTitle"' in source
        and bool(re.search(safe_pattern, source))
    )

    if vulnerable:
        add_result(
            "Статическая проверка XSS",
            "FAIL",
            "Обнаружена известная уязвимая конструкция: "
            "playlist.name вставляется в HTML-шаблон."
        )

    elif protected:
        add_result(
            "Статическая проверка XSS",
            "PASS",
            "Найдено исправление: название плейлиста "
            "выводится через textContent. "
            "Это статическая проверка исходного кода."
        )

    else:
        add_result(
            "Статическая проверка XSS",
            "WARNING",
            "Известное исправление не найдено. "
            "Требуется дополнительная проверка."
        )


def check_xss_browser():
    print("\n" + "-" * 45)
    print("Запуск браузерной проверки Stored XSS")
    print("-" * 45)

    try:
        browser_result = check_xss()

        add_result(
            "Автоматическая проверка Stored XSS",
            browser_result["status"],
            browser_result["description"]
        )

    except Exception as error:
        add_result(
            "Автоматическая проверка Stored XSS",
            "ERROR",
            f"Не удалось выполнить браузерную проверку: {error}"
        )


def save_report():
    report = {
        "project": "Musnews",
        "scanner_version": "1.1",
        "created_at": (
            datetime.now()
            .astimezone()
            .isoformat(timespec="seconds")
        ),
        "target": BASE_URL,
        "checks": results,
        "summary": {
            "total": len(results),
            "passed": sum(
                item["status"] == "PASS"
                for item in results
            ),
            "failed": sum(
                item["status"] == "FAIL"
                for item in results
            ),
            "warnings": sum(
                item["status"] == "WARNING"
                for item in results
            ),
            "errors": sum(
                item["status"] == "ERROR"
                for item in results
            )
        }
    }

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

    print("\n" + "=" * 45)
    print("ИТОГОВЫЕ РЕЗУЛЬТАТЫ")
    print("=" * 45)

    print(f"Всего проверок: {len(results)}")
    print(f"Успешно: {report['summary']['passed']}")
    print(f"Проблем обнаружено: {report['summary']['failed']}")
    print(f"Предупреждений: {report['summary']['warnings']}")
    print(f"Ошибок выполнения: {report['summary']['errors']}")
    print(f"\nОтчёт сохранён: {REPORT_FILE}")


def main():
    results.clear()

    parsed = urlparse(BASE_URL)

    if (
        parsed.scheme not in ("http", "https")
        or parsed.hostname not in (
            "localhost",
            "127.0.0.1",
            "::1"
        )
    ):
        print(
            "Ошибка: сканер разрешено запускать "
            "только для локального сервера."
        )
        return

    print("=" * 45)
    print("MUSNEWS SECURITY SCANNER 1.1")
    print("=" * 45)
    print(f"Адрес сервера: {BASE_URL}")

    server_available = check_server()

    if server_available:
        check_tracks_access()
        check_playlists_access()
    else:
        add_result(
            "Проверки API",
            "ERROR",
            "Проверки API пропущены: сервер недоступен."
        )

    check_xss_source()

    if server_available:
        check_xss_browser()
    else:
        add_result(
            "Автоматическая проверка Stored XSS",
            "ERROR",
            "Браузерная проверка пропущена: сервер недоступен."
        )

    try:
        save_report()
    except OSError as error:
        print(f"Ошибка сохранения отчёта: {error}")


if __name__ == "__main__":
    main()
