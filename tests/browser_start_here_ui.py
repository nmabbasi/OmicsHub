#!/usr/bin/env python3
"""Responsive and no-JavaScript safeguards for the pictured Start Here sections."""
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
SCREENSHOT_SECTIONS = (
    ("#sh-foundation", "entry-route"),
    ("#sh-routes", "research-entry-points"),
    ("#sh-curriculum", "readiness-tracks-hpc-and-reflection"),
    ("#sh-progress-checks", "progress-self-check"),
    ("#sh-catalogue", "browse-all-tutorials"),
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://127.0.0.1:8767")
    parser.add_argument("--browser", default="/opt/google/chrome/chrome")
    parser.add_argument("--output", type=Path, default=Path("/tmp/omics-start-here-review"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    results = {"layouts": [], "interactions": [], "sectionScreenshots": [], "errors": [], "passed": False}

    def check(value, message):
        if not value:
            raise AssertionError(message)

    def block_remote(context):
        context.route("https://**/*", lambda route: route.abort())

    def dismiss_analytics_prompt(page):
        decline = page.get_by_role("button", name="Decline analytics", exact=True)
        if decline.count() and decline.first.is_visible():
            decline.first.click()
            page.wait_for_timeout(80)

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
                dismiss_analytics_prompt(page)
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
                  const main=document.querySelector('main'), hero=main.querySelector('.sh-hero');
                  const heroRect=hero.getBoundingClientRect();
                  const images=[...main.querySelectorAll('img')].map(img=>({src:img.getAttribute('src'),alt:img.alt,
                    loaded:img.complete && img.naturalWidth>0,width:img.naturalWidth}));
                  const routeCards=[...main.querySelectorAll('a.sh-route-card')].map(a=>{
                    const r=a.getBoundingClientRect(), s=getComputedStyle(a);
                    return {href:a.getAttribute('href'),left:r.left,right:r.right,top:r.top,bottom:r.bottom,
                      width:r.width,height:r.height,visible:a.checkVisibility(),display:s.display,boxShadow:s.boxShadow};
                  });
                  const colors=[...main.querySelectorAll('#sh-routes .sh-route-body p,#sh-curriculum .sh-ready-summary,#sh-curriculum .sh-track-summary,#sh-curriculum .sh-hpc-intro p,#sh-curriculum .sh-checkpoint p,#sh-catalogue .sh-catalogue-inner p')]
                    .map(el=>getComputedStyle(el).color);
                  const h1=main.querySelector('h1');
                  const firstReady=main.querySelector('#sh-curriculum .sh-ready-card');
                  const firstTrack=main.querySelector('#sh-curriculum .sh-track-card');
                  const progress=main.querySelector('#sh-progress-checks');
                  const catalogue=main.querySelector('#sh-catalogue');
                  return {viewport:innerWidth,scrollWidth:document.documentElement.scrollWidth,
                    heroBounds:{left:heroRect.left,right:heroRect.right,width:heroRect.width},
                    title:document.title,h1:h1?.innerText,images,routeCards,readerColors:colors,
                    steps:main.querySelectorAll('a.sh-step').length,
                    loopMaps:main.querySelectorAll('.sh-loop-map').length,
                    loopStages:main.querySelectorAll('ol.sh-loop-steps > li.sh-loop-stage').length,
                    loopArrows:main.querySelectorAll('.sh-loop-arrow').length,
                    startHere:main.querySelectorAll('a.sh-step--start').length,
                    sideSteps:main.querySelectorAll('.sh-side-step-nav a').length,
                    languageCards:main.querySelectorAll('.sh-language-card').length,
                    rFirst:main.querySelectorAll('.sh-language-card--recommended').length,
                    pythonAlternative:main.querySelectorAll('.sh-language-card--alternative').length,
                    setupCards:main.querySelectorAll('#sh-curriculum .sh-ready-card').length,
                    setupDisclosures:main.querySelectorAll('#sh-curriculum details.sh-ready-more').length,
                    routeTracks:main.querySelectorAll('#sh-curriculum .sh-track-card').length,
                    routeStages:main.querySelectorAll('#sh-curriculum .sh-track-steps li').length,
                    hpcLinks:main.querySelectorAll('#sh-curriculum .sh-hpc-steps a').length,
                    checkpoints:main.querySelectorAll('#sh-progress-checks .sh-checkpoint').length,
                    catalogueHref:main.querySelector('#sh-catalogue .sh-btn-dark')?.getAttribute('href'),
                    visual:{routeGrid:getComputedStyle(main.querySelector('#sh-routes .sh-routes-grid')).gridTemplateColumns,
                      readyShadow:firstReady?getComputedStyle(firstReady).boxShadow:'missing',
                      trackShadow:firstTrack?getComputedStyle(firstTrack).boxShadow:'missing',
                      progressBackground:progress?getComputedStyle(progress).backgroundColor:'missing',
                      catalogueBackground:catalogue?getComputedStyle(catalogue.querySelector('.sh-catalogue-inner')).backgroundColor:'missing'},
                    words:main.innerText.trim().split(/\\s+/).length};
                }""")
                check(data["scrollWidth"] <= width + 1, f"{width}px: horizontal overflow ({data['scrollWidth']})")
                check(abs(data["heroBounds"]["left"]) <= 1 and abs(data["heroBounds"]["right"] - width) <= 1 and abs(data["heroBounds"]["width"] - width) <= 1, f"{width}px: historical page heading banner must span edge-to-edge")
                check(data["h1"] and "biology" in data["h1"].lower(), f"{width}px: historical page heading missing")
                check({item["src"] for item in data["images"]} == EXPECTED_IMAGES, f"{width}px: original images missing or changed")
                check(all(item["loaded"] and item["alt"].strip() for item in data["images"]), f"{width}px: image failed or lacks alt text")
                check(len(data["routeCards"]) == 4 and all(card["visible"] for card in data["routeCards"]), f"{width}px: research entry points missing")
                check(all(card["left"] >= -1 and card["right"] <= width + 1 for card in data["routeCards"]), f"{width}px: research entry point escapes viewport")
                check(data["steps"] == 4, f"{width}px: foundation steps missing")
                check(data["loopMaps"] == 1 and data["loopStages"] == 4 and data["loopArrows"] == 4, f"{width}px: learning loop is incomplete")
                check(data["startHere"] == 1, f"{width}px: one obvious starting point is required")
                check(data["sideSteps"] == 3, f"{width}px: optional side-step navigation is incomplete")
                check(data["languageCards"] == 2 and data["rFirst"] == 1 and data["pythonAlternative"] == 1, f"{width}px: R/Python branch hierarchy is missing")
                check(data["setupCards"] == 3 and data["setupDisclosures"] == 3, f"{width}px: setup items/disclosures missing")
                check(data["routeTracks"] == 3 and data["routeStages"] == 14, f"{width}px: study tracks/stages missing")
                check(data["hpcLinks"] == 4, f"{width}px: optional HPC route incomplete")
                check(data["checkpoints"] == 3, f"{width}px: progress self-check prompts missing")
                check(data["catalogueHref"] == "tutorials.html", f"{width}px: browse-all-tutorials destination changed")
                check(all("rgba(0, 0, 0, 0)" not in color for color in data["readerColors"]), f"{width}px: reader-facing text became transparent")
                check("Start Here" in data["title"], f"{width}px: page title missing")
                if width in (1440, 390):
                    page.evaluate("window.scrollTo(0, 0)")
                    page.wait_for_timeout(100)
                    label = "desktop" if width == 1440 else "phone"
                    full = args.output / f"start-here-{label}.png"
                    page.add_style_tag(content=".reader-tools, #cookie-consent-banner { display: none !important; }")
                    page.screenshot(path=str(full), full_page=True, animations="disabled")
                    results["sectionScreenshots"].append(str(full))
                    page.add_style_tag(content="header.sticky.top-0 { display: none !important; }")
                    for selector, name in SCREENSHOT_SECTIONS:
                        section = page.locator(selector)
                        section.scroll_into_view_if_needed()
                        section.wait_for(state="visible")
                        output = args.output / f"{name}-{label}.png"
                        section.screenshot(path=str(output), animations="disabled")
                        results["sectionScreenshots"].append(str(output))
                    if width in (1440, 390):
                        page.locator('a.sh-btn[href="#sh-foundation"]').click()
                        check(page.url.endswith("#sh-foundation"), f"{width}px: native learning-path link failed")
                        check(page.locator("#sh-foundation").is_visible(), f"{width}px: foundation section unavailable")
                        results["interactions"].append(f"{width}px native foundation anchor")
                results["layouts"].append(data)
                context.close()
                print(f"PASS Start Here at {width}px: 4 research entries, 4-step loop, 3 readiness items, 3 study tracks, optional HPC, reflection, and catalogue; no overflow", flush=True)

            context = browser.new_context(java_script_enabled=False, viewport={"width": 390, "height": 844})
            block_remote(context)
            page = context.new_page()
            page.goto(args.base + "/start-here.html", wait_until="domcontentloaded")
            check(page.locator("main#main-content").is_visible(), "No-JS main content is unavailable")
            check(page.locator("a.sh-route-card").count() == 4, "No-JS research entry points are unavailable")
            check(page.locator('#sh-catalogue a[href="tutorials.html"]').is_visible(), "No-JS catalogue destination is unavailable")
            check(page.locator('a.sh-btn[href="#sh-foundation"]').get_attribute("href") == "#sh-foundation", "No-JS native learning path link missing")
            check(page.locator(".sh-loop-map").is_visible(), "No-JS learning loop is unavailable")
            check(page.locator("a.sh-step").count() == 4, "No-JS foundation links are unavailable")
            check(page.locator("[data-sh-step]").count() == 0, "Obsolete scripted step controls returned")
            setup_disclosures = page.locator("#sh-curriculum details.sh-ready-more")
            check(setup_disclosures.count() == 3, "No-JS setup disclosures are missing")
            for disclosure in setup_disclosures.all():
                summary = disclosure.locator("summary")
                summary.focus()
                summary.press("Enter")
                check(disclosure.get_attribute("open") is not None, "No-JS setup disclosure cannot be opened natively")
                check(disclosure.locator("a").count() > 0 or disclosure.locator(".sh-ready-detail").is_visible(), "No-JS setup detail is inaccessible")
            route_disclosures = page.locator("#sh-curriculum details.sh-track-details")
            check(route_disclosures.count() == 3, "No-JS study route disclosures are missing")
            for disclosure in route_disclosures.all():
                summary = disclosure.locator("summary")
                summary.focus()
                summary.press("Enter")
                check(disclosure.get_attribute("open") is not None, "No-JS study route disclosure cannot be opened natively")
                check(disclosure.locator("a").count() > 0 and disclosure.locator("a").first.is_visible(), "No-JS study route links are inaccessible")
            check(page.locator("#sh-progress-checks .sh-checkpoint").count() == 3, "No-JS self-check prompts are unavailable")
            results["interactions"].append("native no-JS links, setup/track disclosures, reflection prompts, and catalogue destination")
            context.close()
            browser.close()
        check(not results["errors"], str(results["errors"]))
        results["passed"] = True
    except Exception as error:
        results["failure"] = str(error)
        raise
    finally:
        (args.output / "start-here-browser-results.json").write_text(json.dumps(results, indent=2) + "\n")
    print(f"PASS: {len(results['layouts'])} responsive layouts, {len(results['interactions'])} navigation checks, and {len(results['sectionScreenshots'])} screenshots", flush=True)


if __name__ == "__main__":
    main()
