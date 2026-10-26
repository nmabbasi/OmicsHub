#!/usr/bin/env python3
"""Sitewide circular back-to-top browser regression; all external requests are blocked.

Run with a local static server on port 8767:
  python3 tests/browser_sitewide_top_ui.py
Requires Playwright and Chromium; no screenshots or site DOM modifications are made.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
from route_migration_baseline import published_tutorial_paths
ROOT_PAGES = (
    "index.html", "start-here.html", "tutorials.html", "about.html",
    "contact.html", "services.html", "success.html", "404.html",
)
VIEWPORTS = ((1440, 1000), (390, 844))
INTERACTION_PAGES = (
    "index.html", "tutorials.html", "services.html", "pages/privacy.html",
    "start-here.html", "tutorials/introduction-to-bioinformatics.html",
)


def canonical_pages() -> list[str]:
    return sorted([*ROOT_PAGES, *(p.relative_to(ROOT).as_posix() for p in published_tutorial_paths(ROOT)), *(f"pages/{p.name}" for p in (ROOT / "pages").glob("*.html"))])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://127.0.0.1:8767")
    parser.add_argument("--browser", default="/opt/google/chrome/chrome")
    parser.add_argument("--output", type=Path, default=Path("/tmp/omics-sitewide-top-ui"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    pages = canonical_pages()
    if len(pages) != 70:
        raise AssertionError(f"Expected 70 canonical display pages, found {len(pages)}")
    results: dict[str, object] = {"canonical_pages": len(pages), "layouts": [], "interactions": [], "edge_cases": [], "errors": []}

    def check(condition: bool, message: str) -> None:
        if not condition:
            raise AssertionError(message)

    def block_external(context) -> None:
        host = urlparse(args.base).hostname

        def route_request(route):
            if urlparse(route.request.url).hostname == host:
                route.continue_()
            else:
                route.abort()

        context.route("**/*", route_request)

    def wait_ready(page, path: str) -> None:
        response = page.goto(f"{args.base}/{path}", wait_until="domcontentloaded")
        check(response is not None and response.status == 200, f"{path}: HTTP response {getattr(response, 'status', None)}")
        page.wait_for_selector("#back-to-top", state="attached", timeout=10000)
        page.wait_for_function("""() => {
          const a=document.querySelector('#back-to-top'), w=a?.closest('.tutorial-top-tools');
          return !!w && getComputedStyle(a).backgroundColor === 'rgb(18, 59, 93)' && getComputedStyle(a).borderRadius === '50%';
        }""", timeout=10000)
        decline = page.get_by_role("button", name="Decline analytics", exact=True)
        if decline.is_visible():
            decline.click()

    def find_safe_scroll(page, path: str, width: int, height: int) -> bool:
        dimensions = page.evaluate("() => ({height: document.documentElement.scrollHeight, viewport: innerHeight})")
        max_scroll = max(0, dimensions["height"] - height)
        if max_scroll < 240:
            return False
        for y in range(240, max_scroll + 1, 36):
            page.evaluate("y => scrollTo({top:y,behavior:'instant'})", y)
            page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
            circle = page.locator("#back-to-top")
            if circle.is_visible():
                geometry = circle.evaluate("e => { const r=e.getBoundingClientRect(); return {x:r.x,y:r.y,w:r.width,h:r.height,right:r.right,bottom:r.bottom,position:getComputedStyle(e.parentElement).position}; }")
                check(geometry["position"] == "fixed", f"{path} at {width}px: circle is not floating")
                check(geometry["w"] == geometry["h"] and geometry["w"] >= 48, f"{path} at {width}px: invalid circle geometry {geometry}")
                check(geometry["x"] >= 0 and geometry["y"] >= 0 and geometry["right"] <= width and geometry["bottom"] <= height, f"{path} at {width}px: circle outside viewport")
                safe = page.evaluate("""() => {
                  const a=document.querySelector('#back-to-top'), r=a.getBoundingClientRect();
                  const overlap=e=>{const b=e.getBoundingClientRect();return b.width>0&&b.height>0&&b.left<r.right+7&&b.right>r.left-7&&b.top<r.bottom+7&&b.bottom>r.top-7;};
                  const controls=[...document.querySelectorAll('body a[href],body button,body summary,body input,body select,body textarea,body [tabindex]')].filter(e=>e!==a);
                  if(controls.some(overlap))return false;
                  const texts=document.querySelectorAll('body h1,body h2,body h3,body h4,body h5,body h6,body p,body li,body pre,body figcaption,body td,body th,body blockquote,body label,body dt,body dd,body address');
                  return ![...texts].some(e=>{if(!e.getClientRects().length)return false;const range=document.createRange();range.selectNodeContents(e);return [...range.getClientRects()].some(b=>b.width>0&&b.height>0&&b.left<r.right+7&&b.right>r.left-7&&b.top<r.bottom+7&&b.bottom>r.top-7);});
                }""")
                check(safe, f"{path} at {width}px: control is not in a safe content gap")
                return True
        return False

    try:
        with sync_playwright() as pw:
            launch = {"headless": True, "args": ["--no-sandbox"]}
            if args.browser:
                launch["executable_path"] = args.browser
            browser = pw.chromium.launch(**launch)
            for width, height in VIEWPORTS:
                context = browser.new_context(viewport={"width": width, "height": height}, reduced_motion="reduce")
                block_external(context)
                page = context.new_page()
                page.on("pageerror", lambda error: results["errors"].append(str(error)))
                for path in pages:
                    wait_ready(page, path)
                    check(page.locator("#back-to-top").count() == 1, f"{path} at {width}px: missing/duplicate circle")
                    data = page.evaluate("""() => {
                      const a=document.querySelector('#back-to-top'), w=a.closest('.tutorial-top-tools'), s=getComputedStyle(a);
                      const title=document.getElementById(a.hash.slice(1));
                      return {width:innerWidth,height:innerHeight,hiddenInitially:w.hidden,
                        bg:s.backgroundColor,border:s.borderTopColor,radius:s.borderRadius,
                        cssWidth:s.width,cssHeight:s.height,anchor:a.tagName,href:a.getAttribute('href'),
                        icon:a.querySelector('.tutorial-top-icon svg path')?.getAttribute('d'),
                        label:a.getAttribute('aria-label'),targetCount:title?document.querySelectorAll(`[id="${CSS.escape(title.id)}"]`).length:0,
                        topIdCount:document.querySelectorAll('#back-to-top').length};
                    }""")
                    expected_size = "52px" if width <= 639 else "56px"
                    check(data["hiddenInitially"], f"{path} at {width}px: circle shown before scroll")
                    check(data["bg"] == "rgb(18, 59, 93)" and data["border"] == "rgb(140, 221, 207)", f"{path} at {width}px: wrong shared navy/teal colors: {data}")
                    check(data["radius"] == "50%" and data["cssWidth"] == expected_size and data["cssHeight"] == expected_size, f"{path} at {width}px: wrong shared circle dimensions: {data}")
                    check(data["anchor"] == "A" and data["href"].startswith("#") and data["icon"] == "M12 19V5m-6 6 6-6 6 6", f"{path} at {width}px: not the expected native arrow anchor: {data}")
                    check(data["label"] == "Back to top" and data["targetCount"] == 1 and data["topIdCount"] == 1, f"{path} at {width}px: missing or duplicate target/control: {data}")
                    scrollable = page.evaluate("() => document.documentElement.scrollHeight > innerHeight + 240")
                    if scrollable:
                        check(find_safe_scroll(page, path, width, height), f"{path} at {width}px: no safe visible scroll gap")
                    else:
                        check(not find_safe_scroll(page, path, width, height), f"{path} at {width}px: unexpectedly scrollable short page")
                    results["layouts"].append({"path": path, "width": width, "height": height, "scrollable": scrollable})
                context.close()
                print(f"PASS {len(pages)} canonical pages at {width}px", flush=True)

            for width, height in VIEWPORTS:
                context = browser.new_context(viewport={"width": width, "height": height}, reduced_motion="reduce")
                block_external(context)
                page = context.new_page()
                for path in INTERACTION_PAGES:
                    wait_ready(page, path)
                    check(find_safe_scroll(page, path, width, height), f"{path} at {width}px: no safe place to test keyboard return")
                    anchor = page.locator("#back-to-top")
                    anchor.focus()
                    page.keyboard.press("Enter")
                    target_id = anchor.get_attribute("href")[1:]
                    page.wait_for_function("id => location.hash === '#' + id && document.activeElement?.id === id && scrollY < 300", arg=target_id)
                    check(page.evaluate("id => document.getElementById(id)?.tabIndex === -1", target_id), f"{path} at {width}px: target not focusable after return")
                    page.wait_for_function("document.querySelector('.tutorial-top-tools').hidden")
                    results["interactions"].append({"path": path, "width": width, "keyboard": "Enter", "focus_return": target_id})
                context.close()
            context = browser.new_context(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
            block_external(context)
            page = context.new_page()
            page.on("pageerror", lambda error: results["errors"].append(str(error)))
            missing_url = f"{args.base}/__missing__/nested/page"
            page.route(missing_url, lambda route: route.fulfill(status=404, content_type="text/html", body=(ROOT / "404.html").read_text(encoding="utf-8")))
            response = page.goto(missing_url, wait_until="domcontentloaded")
            check(response.status == 404, "Nested 404 fallback was not served as a missing page")
            page.wait_for_function("""() => {
              const a=document.querySelector('#back-to-top');
              return a && getComputedStyle(a).backgroundColor === 'rgb(18, 59, 93)' && getComputedStyle(a).borderRadius === '50%';
            }""", timeout=10000)
            check(page.locator('#back-to-top').count() == 1, 'Nested 404 fallback lacks one correctly loaded arrow')
            results["edge_cases"].append({"check": "nested missing-URL 404 loads root-resolving shared arrow", "passed": True})
            context.close()
            browser.close()
        check(not results["errors"], f"Browser errors: {results['errors']}")
        results["passed"] = True
    except Exception as error:
        results["passed"] = False
        results["failure"] = str(error)
        raise
    finally:
        (args.output / "sitewide-top-ui-results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: {len(results['layouts'])} page/layout checks, {len(results['interactions'])} keyboard/focus interactions, and {len(results['edge_cases'])} nested-404 check", flush=True)


if __name__ == "__main__":
    main()
