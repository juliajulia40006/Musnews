
import json
from datetime import datetime
from pathlib import Path

from playwright.sync_api import (
    sync_playwright,
    Error
)


BASE_URL = "http://localhost:5000"

SCANNER_DIR = Path(__file__).resolve().parent

REPORT_FILE = SCANNER_DIR / "xss_report.json"
SCREENSHOT_FILE = SCANNER_DIR / "xss_result.png"

PLAYLIST_NAME = "Музыка для отдыха"


def check_xss():
    result = {
        "check": "Stored XSS в общих плейлистах",
        "date": datetime.now().isoformat(
            timespec="seconds"
        ),
        "status": "ERROR",
        "description": ""
    }

    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(
                headless=False
            )

        except Error as error:
            result["description"] = (
                f"Не удалось открыть Chromium: {error}"
            )
            return result

        try:
            page = browser.new_page()

            page.goto(
                BASE_URL + "/login.html",
                wait_until="domcontentloaded",
                timeout=15000
            )

            print("\nОткрылся браузер Chromium.")
            print(
                "Войди в свой ТЕСТОВЫЙ аккаунт Musnews."
            )
            print(
                "Дождись появления главной страницы."
            )

            input(
                "\nПосле входа вернись в терминал "
                "и нажми Enter..."
            )

            # Дожидаемся перехода после авторизации
            page.wait_for_url(
                "**/index.html*",
                timeout=30000
            )

            print("\nАвторизация подтверждена.")
            print("Ищем тестовый плейлист...")

            page.wait_for_selector(
                "#sharedPlaylists",
                timeout=10000
            )

            playlists = (
                page.locator("#sharedPlaylists li")
                .filter(has_text=PLAYLIST_NAME)
            )

            if playlists.count() == 0:
                result["status"] = "SKIP"
                result["description"] = (
                    f"Плейлист '{PLAYLIST_NAME}' "
                    "не найден. Проверка пропущена."
                )
                return result

            print("\nНайден тестовый плейлист.")
            print("Открываем его автоматически...")

            playlists.first.click()

            # Даём браузеру выполнить обработчики
            page.wait_for_timeout(1500)

            attack_executed = (
                page.locator("#xss-screen").count() > 0
            )

            safe_title = page.locator(
                "#safePlaylistTitle"
            )

            displayed_text = ""

            if safe_title.count() > 0:
                displayed_text = (
                    safe_title.first.text_content() or ""
                )

            # Сохраняем скриншот проверки
            page.screenshot(
                path=str(SCREENSHOT_FILE),
                full_page=True
            )

            if attack_executed:
                result["status"] = "FAIL"
                result["description"] = (
                    "Обнаружено выполнение XSS-атаки. "
                    "На странице появился элемент "
                    "xss-screen."
                )

            elif (
                "<img" in displayed_text
                and "onerror" in displayed_text
            ):
                result["status"] = "PASS"
                result["description"] = (
                    "XSS-код отображается как текст. "
                    "Внедрённый скрипт не выполнился."
                )

            else:
                result["status"] = "WARNING"
                result["description"] = (
                    "Выполнение XSS не обнаружено, "
                    "но тестовая конструкция "
                    "не подтверждена в названии "
                    "открытого плейлиста."
                )

        except Error as error:
            result["status"] = "ERROR"
            result["description"] = (
                f"Ошибка Playwright: {error}"
            )

        except (OSError, EOFError) as error:
            result["status"] = "ERROR"
            result["description"] = (
                f"Ошибка выполнения проверки: {error}"
            )

        finally:
            browser.close()

    return result


def main():
    print("=" * 45)
    print("MUSNEWS — АВТОМАТИЧЕСКАЯ ПРОВЕРКА XSS")
    print("=" * 45)

    result = check_xss()

    print(f"\n[{result['status']}]")
    print(result["description"])

    try:
        with REPORT_FILE.open(
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                result,
                file,
                ensure_ascii=False,
                indent=4
            )

        print(f"\nОтчёт сохранён: {REPORT_FILE}")

    except OSError as error:
        print(f"Ошибка сохранения отчёта: {error}")


if __name__ == "__main__":
    main()