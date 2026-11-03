
import json
import re
import secrets
import urllib.error
import urllib.request

from datetime import datetime
from pathlib import Path
from urllib.parse import quote, urlparse


BASE_URL = "http://localhost:5000"

SCANNER_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCANNER_DIR.parent

REPORT_FILE = SCANNER_DIR / "sql_report.json"


def result(name: str, status: str, description: str) -> dict[str, str]:
    print(f"\n[{status}] {name}")
    print(description)

    return {
        "name": name,
        "status": status,
        "description": description
    }


def request_status(
    path: str,
    payload: dict[str, str] | None = None
) -> tuple[int | None, str | None]:

    data = (
        json.dumps(payload).encode("utf-8")
        if payload is not None
        else None
    )

    headers = {
        "User-Agent": "Musnews-SQL-Scanner/1.0"
    }

    if data is not None:
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        BASE_URL.rstrip("/") + path,
        data=data,
        headers=headers,
        method="POST" if data is not None else "GET"
    )

    try:
        with urllib.request.urlopen(
            request, timeout=8
        ) as response:
            return response.status, None

    except urllib.error.HTTPError as error:
        return error.code, None

    except (
        urllib.error.URLError,
        TimeoutError,
        OSError
    ) as error:
        return None, str(error)


def check_sql_source() -> dict[str, str]:
    source_files = []

    folders = (
        PROJECT_DIR / "Musnews.Server",
        PROJECT_DIR / "Musnews.Data"
    )

    for folder in folders:
        if not folder.is_dir():
            return result(
                "SQL: анализ исходного кода",
                "ERROR",
                f"Не найдена папка: {folder}"
            )

        for file in folder.rglob("*.cs"):
            if not any(
                part.lower() in {"obj", "bin"}
                for part in file.parts
            ):
                source_files.append(file)

    suspicious_calls = re.compile(
        r"\b(?:FromSqlRaw|ExecuteSqlRaw|SqlQueryRaw"
        r"|SqliteCommand|SqlCommand|CreateCommand)\b"
    )

    matches = []

    for file in source_files:
        
        try:
            try:
                text = file.read_text(encoding="utf-8-sig")
            except UnicodeDecodeError:
                text = file.read_text(encoding="cp1251")

        except (OSError, UnicodeError) as error:

            return result(
                "SQL: анализ исходного кода",
                "ERROR",
                f"Ошибка чтения {file.name}: {error}"
            )

        if suspicious_calls.search(text):
            matches.append(
                str(file.relative_to(PROJECT_DIR))
            )

    if matches:
        return result(
            "SQL: анализ исходного кода",
            "WARNING",
            "Найдены вызовы, требующие ручного "
            "анализа параметризации: "
            + ", ".join(matches)
        )

    return result(
        "SQL: анализ исходного кода",
        "PASS",
        f"Проверено C#-файлов: {len(source_files)}. "
        "Известные вызовы прямого SQL не найдены. "
        "Это не доказывает отсутствие всех SQL-инъекций."
    )


def check_playlist_id() -> dict[str, str]:
    baseline_status, baseline_error = request_status(
        "/api/playlists/2147483647"
    )

    injection = quote(
        "' OR 1=1 --",
        safe=""
    )

    attack_status, attack_error = request_status(
        f"/api/playlists/{injection}"
    )

    if baseline_error or attack_error:
        return result(
            "SQL: параметр ID плейлиста",
            "ERROR",
            f"Сбой подключения: "
            f"{baseline_error or attack_error}"
        )

    if baseline_status != 404:
        return result(
            "SQL: параметр ID плейлиста",
            "WARNING",
            f"Контрольный запрос вернул "
            f"HTTP {baseline_status}, ожидался 404. "
            "Результат проверки неоднозначен."
        )

    if attack_status in (400, 404):
        return result(
            "SQL: параметр ID плейлиста",
            "PASS",
            "Подозрительное значение отклонено "
            f"(HTTP {attack_status}); "
            "контрольный неизвестный ID вернул HTTP 404."
        )

    if attack_status == 200:
        return result(
            "SQL: параметр ID плейлиста",
            "WARNING",
            "Сервер вернул HTTP 200 на SQL-подобный ввод. "
            "Нужно проверить тело ответа вручную."
        )

    return result(
        "SQL: параметр ID плейлиста",
        "WARNING",
        f"Неожиданный ответ HTTP {attack_status}; "
        "необходима ручная проверка."
    )


def check_login_input() -> dict[str, str]:
    fake_user = (
        "__sql_test_"
        + secrets.token_hex(6)
        + "' OR '1'='1' --"
    )

    fake_password = secrets.token_hex(20)

    status, error = request_status(
        "/api/auth/login",
        {
            "username": fake_user,
            "password": fake_password
        }
    )

    if error:
        return result(
            "SQL: поле логина",
            "ERROR",
            error
        )

    if status == 401:
        return result(
            "SQL: поле логина",
            "PASS",
            "Попытка входа с SQL-подобным именем "
            "отклонена (HTTP 401)."
        )

    if status == 200:
        return result(
            "SQL: поле логина",
            "FAIL",
            "Сервер ответил HTTP 200 на заведомо "
            "неверные учётные данные. "
            "Проверь авторизацию вручную; "
            "это ещё не доказательство SQL-инъекции."
        )

    return result(
        "SQL: поле логина",
        "WARNING",
        f"Получен HTTP {status} вместо ожидаемого 401. "
        "Проверь логи приложения."
    )


def main() -> None:
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
            "Ошибка: разрешена проверка "
            "только локального Musnews."
        )
        return

    print("=" * 48)
    print("MUSNEWS SQL SECURITY CHECK 1.0")
    print("=" * 48)
    print(f"Сервер: {BASE_URL}")

    checks = [
        check_sql_source(),
        check_playlist_id(),
        check_login_input()
    ]

    report = {
        "project": "Musnews",
        "created_at": (
            datetime.now()
            .astimezone()
            .isoformat(timespec="seconds")
        ),
        "checks": checks
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

    except OSError as error:
        print(
            f"Не удалось записать отчёт: {error}"
        )
        return

    print("\n" + "=" * 48)
    print(f"Проверок выполнено: {len(checks)}")
    print(f"Отчёт сохранён: {REPORT_FILE}")


if __name__ == "__main__":
    main()
