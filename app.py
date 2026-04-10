import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path


def load_config(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def setup_logging(log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def save_page_snapshot(page, save_dir: Path, cycle: int) -> None:
    save_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_path = save_dir / f"page_{timestamp}_{cycle}.html"
    screenshot_path = save_dir / f"screenshot_{timestamp}_{cycle}.png"
    try:
        html = page.content()
        html_path.write_text(html, encoding="utf-8")
        page.screenshot(path=str(screenshot_path), full_page=True)
        logging.info(f"Saved HTML to {html_path} and screenshot to {screenshot_path}")
    except Exception as exc:
        logging.warning(f"Unable to save snapshot: {exc}")


def request_new_tor_identity(host: str, port: int, password: str | None) -> bool:
    try:
        from stem import Signal
        from stem.control import Controller
    except ImportError:
        logging.warning("stem is not installed. Skipping Tor NEWNYM identity change.")
        return False

    try:
        with Controller.from_port(address=host, port=port) as controller:
            controller.authenticate(password=password or None)
            controller.signal(Signal.NEWNYM)
            logging.info("Requested new Tor identity (NEWNYM).")
            return True
    except Exception as exc:
        logging.warning(f"Could not request Tor identity change: {exc}")
        return False


def find_and_click_button(page, button_text: str) -> bool:
    normalized_text = button_text.strip()

    selectors = [
        f"button:has-text(\"{normalized_text}\")",
        f"a:has-text(\"{normalized_text}\")",
        f"[role=button]:has-text(\"{normalized_text}\")",
        f"input[type=submit][value*='{normalized_text}']",
        f"input[type=button][value*='{normalized_text}']",
    ]

    locator = page.get_by_text(normalized_text, exact=False)
    if locator.count() > 0:
        try:
            locator.first.click(timeout=10000)
            logging.info(f"Clicked text match for '{normalized_text}'.")
            return True
        except Exception as exc:
            logging.warning(f"Text locator click failed: {exc}")

    for selector in selectors:
        try:
            elm = page.locator(selector)
            if elm.count() > 0:
                elm.first.click(timeout=10000)
                logging.info(f"Clicked selector '{selector}'.")
                return True
        except Exception:
            continue

    logging.warning(f"Unable to find a clickable element containing '{normalized_text}'.")
    return False


def run_cycle(config: dict, cycle: int) -> bool:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logging.error(
            "Playwright is not installed. Install it with: python -m pip install playwright and then playwright install chromium"
        )
        return False

    user_data_dir = Path(config["user_data_dir"]).resolve()
    save_html_dir = Path(config["save_html_dir"]).resolve()
    proxy = {"server": config["tor_proxy"]} if config.get("tor_proxy") else None

    with sync_playwright() as pw:
        logging.info("Launching Chromium with Tor proxy.")
        browser_context = pw.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=bool(config.get("headless", False)),
            proxy=proxy,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
            ignore_https_errors=True,
        )

        try:
            page = browser_context.new_page()
            page.set_default_timeout(int(config.get("timeout_seconds", 60)) * 1000)
            logging.info(f"Navigating to {config['url']}")
            page.goto(config["url"], wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle")

            save_page_snapshot(page, save_html_dir, cycle)
            clicked = find_and_click_button(page, config.get("button_text", "dalyvauti"))

            if not clicked:
                logging.warning("The button was not clicked. The page may have changed or the text is not present.")
            else:
                logging.info("Button click completed.")

            wait_seconds = int(config.get("wait_after_click_seconds", 15))
            if wait_seconds > 0:
                logging.info(f"Waiting {wait_seconds} seconds after click.")
                time.sleep(wait_seconds)

            return True
        except Exception as exc:
            logging.exception(f"Cycle failed: {exc}")
            return False
        finally:
            browser_context.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Tor-based Chromium click automation for lrytas site.")
    parser.add_argument("--config", default="config.json", help="Path to config file")
    parser.add_argument("--once", action="store_true", help="Run a single cycle and exit")
    args = parser.parse_args()

    config_path = Path(args.config)
    config = load_config(config_path)
    setup_logging(Path(config.get("log_file", "app.log")))

    logging.info("Starting automation app.")
    iterations = 0
    max_iterations = int(config.get("max_iterations", 0))
    interval_seconds = int(config.get("click_interval_minutes", 60)) * 60

    while True:
        iterations += 1
        logging.info(f"Starting cycle {iterations}.")
        success = run_cycle(config, iterations)

        if config.get("use_tor_newnym", False):
            request_new_tor_identity(
                host=config.get("tor_control_host", "127.0.0.1"),
                port=int(config.get("tor_control_port", 9051)),
                password=config.get("tor_control_password", "") or None,
            )

        if args.once:
            logging.info("Run-once mode enabled, exiting after first cycle.")
            break

        if max_iterations and iterations >= max_iterations:
            logging.info(f"Reached max_iterations={max_iterations}. Exiting.")
            break

        if interval_seconds > 0:
            logging.info(f"Sleeping {interval_seconds} seconds until next cycle.")
            time.sleep(interval_seconds)
        else:
            logging.info("Interval is 0 or negative; exiting after one cycle.")
            break

    logging.info("Automation app finished.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
