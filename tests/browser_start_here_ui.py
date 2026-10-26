#!/usr/bin/env python3
"""Responsive image-led Start Here checks; remote requests are blocked."""
from pathlib import Path
import argparse
import json
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_IMAGES = {
    "images/sh-three-laptop-learner-banner-with-copy.webp",
    "images/sh-route-single-cell-laptop-v3.webp",
    "images/sh-route-genomics-laptop-v3.webp",
    "images/sh-route-microbial-laptop-v3.webp",
    "images/sh-route-evolution-laptop-v3.webp",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://127.0.0.1:8767")
    parser.add_argument("--browser", default="/opt/google/chrome/chrome")
    parser.add_argument("--output", type=Path, default=Path("/tmp/omics-start-here-image-led"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    results = {"layouts": [], "interactions": [], "errors": [], "passed": False}

    def check(value, message):
        if not value:
            raise AssertionError(message)

    def block_remote(context):
        context.route("https://**/*", lambda route: route.abort())

    try:
        with sync_playwright() as p:
            options = {"headless": True, "args": ["--no-sandbox"]}
            if args.browser:
                options["executable_path"] = args.browser
            browser = p.chromium.launch(**options)
            for width, height in [(1440, 1100), (1024, 900), (768, 900), (390, 844), (320, 640)]:
                context = browser.new_context(
                    viewport={"width": width, "height": height},
                    reduced_motion="reduce",
                )
                context.add_init_script("localStorage.setItem('omicsHubCookieChoice', 'declined')")
                block_remote(context)
                page = context.new_page()
                page.on("pageerror", lambda error: results["errors"].append(str(error)))
                page.goto(args.base + "/start-here.html", wait_until="domcontentloaded")
                page.wait_for_selector("main#main-content")
                images = page.locator("main img")
                check(images.count() == 5, f"{width}px: original image count changed")
                for image in images.all():
                    image.scroll_into_view_if_needed()
                    loaded = False
                    for _ in range(30):
                        if image.evaluate("img => img.complete && img.naturalWidth > 0"):
                            loaded = True
                            break
                        page.wait_for_timeout(100)
                    check(loaded, f"{width}px: an original image did not load")
                data = page.evaluate("""() => {
                  const main=document.querySelector('main'), hero=document.querySelector('.sh-hero');
                  const heroRect=hero.getBoundingClientRect();
                  const images=[...main.querySelectorAll('img')].map(img=>({src:img.getAttribute('src'),alt:img.alt,
                    loaded:img.complete && img.naturalWidth>0,width:img.naturalWidth}));
                  const cards=[...main.querySelectorAll('a.sh-route-card')].map(a=>{
                    const r=a.getBoundingClientRect();
                    return {href:a.getAttribute('href'),left:r.left,right:r.right,top:r.top,bottom:r.bottom,
                      width:r.width,height:r.height,visible:a.checkVisibility()};
                  });
                  const h1=main.querySelector('h1');
                  return {viewport:innerWidth,scrollWidth:document.documentElement.scrollWidth,
                    heroBounds:{left:heroRect.left,right:heroRect.right,width:heroRect.width},
                    title:document.title,h1:h1?.innerText,heroBackground:getComputedStyle(hero).backgroundColor,
                    images,cards,steps:main.querySelectorAll("a.sh-step").length,
                    setupCards:main.querySelectorAll(".sh-ready-card").length,
                    setupDisclosures:main.querySelectorAll("#sh-curriculum details.sh-ready-more").length,
                    routeTracks:main.querySelectorAll(".sh-track-card").length,
                    routeStages:main.querySelectorAll(".sh-track-steps li").length,
                    hpcLinks:main.querySelectorAll(".sh-hpc-steps a").length,
                    orbit:main.querySelectorAll(".sh-orbit,[data-sh-step]").length,
                    words:main.innerText.trim().split(/\\s+/).length};
                }""")
                check(data["scrollWidth"] <= width + 1, f"{width}px: horizontal overflow ({data['scrollWidth']})")
                check(abs(data["heroBounds"]["left"]) <= 1 and abs(data["heroBounds"]["right"] - width) <= 1 and abs(data["heroBounds"]["width"] - width) <= 1, f"{width}px: tutorial banner must span edge-to-edge")
                check(data["h1"] and "biology" in data["h1"].lower(), f"{width}px: historical page heading missing")
                check({item["src"] for item in data["images"]} == EXPECTED_IMAGES, f"{width}px: original images missing or changed")
                check(all(item["loaded"] and item["alt"].strip() for item in data["images"]), f"{width}px: image failed or lacks alt text")
                check(len(data["cards"]) == 4 and all(card["visible"] for card in data["cards"]), f"{width}px: route cards missing")
                check(all(card["left"] >= -1 and card["right"] <= width + 1 for card in data["cards"]), f"{width}px: route card escapes viewport")
                check(data["steps"] == 4, f"{width}px: foundation steps missing")
                check(data["setupCards"] == 3 and data["setupDisclosures"] == 3, f"{width}px: setup cards/disclosures missing")
                check(data["routeTracks"] == 3 and data["routeStages"] == 14, f"{width}px: study tracks/stages missing")
                check(data["hpcLinks"] == 4, f"{width}px: optional HPC route incomplete")
                check(data["orbit"] == 0, f"{width}px: circular path markup returned")
                check("Start Here" in data["title"], f"{width}px: page title missing")
                if width in (1440, 390):
                    page.evaluate("window.scrollTo(0, 0)")
                    page.wait_for_timeout(100)
                    page.screenshot(path=str(args.output / ("start-here-desktop.png" if width == 1440 else "start-here-mobile.png")), full_page=True)
                if width in (1440, 390):
                    page.locator('a.sh-btn[href="#sh-foundation"]').click()
                    check(page.url.endswith("#sh-foundation"), f"{width}px: native learning-path link failed")
                    check(page.locator("#sh-foundation").is_visible(), f"{width}px: foundation section unavailable")
                    results["interactions"].append(f"{width}px native foundation anchor")
                results["layouts"].append(data)
                context.close()
                print(f"PASS Start Here at {width}px: 5 original images, 4 route cards, no horizontal overflow", flush=True)

            context = browser.new_context(
                java_script_enabled=False, viewport={"width": 390, "height": 844}
            )
            block_remote(context)
            page = context.new_page()
            page.goto(args.base + "/start-here.html", wait_until="domcontentloaded")
            check(page.locator("main#main-content").is_visible(), "No-JS main content is unavailable")
            check(page.locator("a.sh-route-card").count() == 4, "No-JS route cards are unavailable")
            check(page.locator('a.sh-btn[href="#sh-foundation"]').get_attribute("href") == "#sh-foundation", "No-JS native learning path link missing")
            check(page.locator(".sh-orbit,[data-sh-step]").count() == 0, "No-JS circular path markup returned")
            check(page.locator("#sh-curriculum details.sh-ready-more").count() == 3, "No-JS setup disclosures are missing")
            for disclosure in page.locator("#sh-curriculum details.sh-ready-more").all():
                disclosure.locator("summary").click()
                check(disclosure.locator("a").count() > 0 or disclosure.locator(".sh-ready-detail").is_visible(), "No-JS setup detail is inaccessible")
            route_disclosures = page.locator("#sh-curriculum details.sh-track-details")
            check(route_disclosures.count() == 3, "No-JS study route disclosures are missing")
            for disclosure in route_disclosures.all():
                disclosure.locator("summary").click()
                check(disclosure.locator("a").count() > 0 and disclosure.locator("a").first.is_visible(), "No-JS study route links are inaccessible")
            results["interactions"].append("native no-JS content, setup disclosures, route disclosures, and image links")
            context.close()
            browser.close()
        check(not results["errors"], str(results["errors"]))
        results["passed"] = True
    except Exception as error:
        results["failure"] = str(error)
        raise
    finally:
        (args.output / "start-here-browser-results.json").write_text(json.dumps(results, indent=2) + "\n")
    print(f"PASS: {len(results['layouts'])} responsive layouts and {len(results['interactions'])} navigation checks", flush=True)


if __name__ == "__main__":
    main()
