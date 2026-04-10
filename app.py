import argparse
import json
import logging
import os
import random
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


def apply_stealth_measures(page, config: dict) -> None:
    """Apply various stealth measures to avoid detection."""
    if not config.get("stealth_mode", False):
        return
    
    # Random user agent
    user_agents = config.get("user_agents", [])
    if user_agents:
        user_agent = random.choice(user_agents)
        page.set_extra_http_headers({"User-Agent": user_agent})
        logging.info(f"Set user agent: {user_agent[:50]}...")
    
    # Random viewport size
    viewport_sizes = config.get("viewport_sizes", [])
    if viewport_sizes:
        viewport = random.choice(viewport_sizes)
        page.set_viewport_size(viewport)
        logging.info(f"Set viewport: {viewport['width']}x{viewport['height']}")
    
    # Random delay before actions
    delay_min = config.get("random_delay_min", 1)
    delay_max = config.get("random_delay_max", 5)
    delay = random.uniform(delay_min, delay_max)
    logging.info(f"Applying random delay: {delay:.1f} seconds")
    time.sleep(delay)
    """Apply various stealth measures to avoid detection."""
    if not config.get("stealth_mode", False):
        return
    
    # Random user agent
    user_agents = config.get("user_agents", [])
    if user_agents:
        user_agent = random.choice(user_agents)
        page.set_extra_http_headers({"User-Agent": user_agent})
        logging.info(f"Set user agent: {user_agent[:50]}...")
    
    # Random viewport size
    viewport_sizes = config.get("viewport_sizes", [])
    if viewport_sizes:
        viewport = random.choice(viewport_sizes)
        page.set_viewport_size(viewport)
        logging.info(f"Set viewport: {viewport['width']}x{viewport['height']}")
    
    # Random delay before actions
    delay_min = config.get("random_delay_min", 1)
    delay_max = config.get("random_delay_max", 5)
    delay = random.uniform(delay_min, delay_max)
    logging.info(f"Applying random delay: {delay:.1f} seconds")
    time.sleep(delay)


def human_like_behavior(page) -> None:
    """Simulate human-like browsing behavior."""
    # Random mouse movements
    try:
        # Move mouse to random positions
        for _ in range(random.randint(2, 5)):
            x = random.randint(100, 1200)
            y = random.randint(100, 800)
            page.mouse.move(x, y)
            time.sleep(random.uniform(0.1, 0.5))
        
        # Random scroll
        scroll_amount = random.randint(200, 800)
        page.evaluate(f"window.scrollBy(0, {scroll_amount})")
        time.sleep(random.uniform(0.5, 1.5))
        
    except Exception as exc:
        logging.debug(f"Human behavior simulation failed: {exc}")


def find_and_click_button(page, button_text: str) -> bool:
    normalized_text = button_text.strip()

    # Debug: log what we find
    locator = page.get_by_text(normalized_text, exact=False)
    logging.info(f"Found {locator.count()} elements containing '{normalized_text}'")
    
    # Debug: count all buttons
    all_buttons = page.locator("button")
    logging.info(f"Found {all_buttons.count()} button elements on page")
    
    if locator.count() > 0:
        element = locator.first
        tag_name = element.evaluate("el => el.tagName")
        classes = element.evaluate("el => el.className")
        logging.info(f"First element: <{tag_name}> with classes: {classes}")
        # Check if it's visible
        is_visible = element.is_visible()
        logging.info(f"Element is visible: {is_visible}")

    # First try to find clickable elements containing the text
    selectors = [
        f"button:has-text(\"{normalized_text}\")",
        f"a:has-text(\"{normalized_text}\")",
        f"[role=button]:has-text(\"{normalized_text}\")",
        f"input[type=submit][value*='{normalized_text}']",
        f"input[type=button][value*='{normalized_text}']",
        # Look for divs or spans that might be clickable and contain the text
        f"div:has-text(\"{normalized_text}\")",
        f"span:has-text(\"{normalized_text}\")",
    ]

    # Try text locator first
    locator = page.get_by_text(normalized_text, exact=False)
    if locator.count() > 0:
        # Get the first element and check if it's clickable
        element = locator.first
        try:
            # Try to click the element directly
            element.click(timeout=5000)
            logging.info(f"Clicked text element containing '{normalized_text}'.")
            return True
        except Exception:
            # If direct click fails, try to find a clickable parent
            try:
                # Look for clickable parent elements
                parent_selectors = ["button", "a", "[role=button]", "input[type=submit]", "input[type=button]", "div[onclick]", "span[onclick]"]
                for parent_sel in parent_selectors:
                    parent = element.locator(f"xpath=ancestor-or-self::{parent_sel}").first
                    if parent.count() > 0:
                        parent.click(timeout=5000)
                        logging.info(f"Clicked parent {parent_sel} containing '{normalized_text}'.")
                        return True
            except Exception:
                pass

    # Try to find any clickable element that might be the vote button
    # Look for common vote button patterns
    vote_selectors = [
        "button:has(svg)",  # Button with icon
        ".vote-button",
        ".btn-vote",
        "[data-action='vote']",
        "[data-testid*='vote']",
    ]
    
    for selector in vote_selectors:
        try:
            elm = page.locator(selector)
            if elm.count() > 0:
                elm.first.click(timeout=5000)
                logging.info(f"Clicked potential vote button with selector '{selector}'.")
                return True
        except Exception:
            continue

    # Try specific selectors
    for selector in selectors:
        try:
            elm = page.locator(selector)
            if elm.count() > 0:
                elm.first.click(timeout=5000)
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
    proxy = None  # Removed Tor proxy

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
            
            # Apply stealth measures
            apply_stealth_measures(page, config)
            
            logging.info(f"Navigating to {config['url']}")
            page.goto(config["url"], wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle")
            
            # Simulate human behavior
            if config.get("stealth_mode", False):
                human_like_behavior(page)
            
            # Wait a bit more for dynamic content
            page.wait_for_timeout(3000)

            save_page_snapshot(page, save_html_dir, cycle)
            clicked = find_and_click_button(page, config.get("button_text", "Balsuoti"))

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
    base_interval = int(config.get("click_interval_minutes", 60)) * 60
    
    while True:
        iterations += 1
        logging.info(f"Starting cycle {iterations}.")
        success = run_cycle(config, iterations)

        if args.once:
            logging.info("Run-once mode enabled, exiting after first cycle.")
            break

        if max_iterations and iterations >= max_iterations:
            logging.info(f"Reached max_iterations={max_iterations}. Exiting.")
            break

        # Use random interval for stealth
        if config.get("stealth_mode", False):
            # Add random variation to base interval (±25%)
            variation = base_interval * 0.25
            interval_seconds = base_interval + random.uniform(-variation, variation)
            interval_seconds = max(60, interval_seconds)  # Minimum 1 minute
        else:
            interval_seconds = base_interval

        if interval_seconds > 0:
            logging.info(f"Sleeping {interval_seconds:.0f} seconds until next cycle.")
            time.sleep(interval_seconds)
        else:
            logging.info("Interval is 0 or negative; exiting after one cycle.")
            break

    logging.info("Automation app finished.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
