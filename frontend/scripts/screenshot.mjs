import { chromium } from "@playwright/test";
const BASE = process.env.FRONTEND_URL ?? "http://localhost:3000";
const OUT = "../docs/assets";
const browser = await chromium.launch();
const page = await browser.newPage({
    viewport: { width: 1440, height: 1000 },
    deviceScaleFactor: 1,
});
await page.addStyleTag({ content: "nextjs-portal{display:none!important}" });
await page.goto(BASE, { waitUntil: "networkidle" });
await page.screenshot({ path: `${OUT}/home.png` });
const prompt = page
    .locator("main")
    .getByRole("button", { name: /我想买一瓶沐浴露/ })
    .first();
await prompt.click();
await page
    .getByRole("button", { name: "View recommendation" })
    .first()
    .waitFor({ timeout: 60000 });
await page
    .getByText(/Mock mode generated an explainable recommendation|Model generated the recommendation and notes/)
    .waitFor({ timeout: 60000 });
await page.waitForTimeout(800);
const scroller = page.locator("main div.overflow-y-auto").first();
await scroller.evaluate((element) => element.scrollTo(0, 0));
await page.waitForTimeout(400);
await page.screenshot({ path: `${OUT}/chat.png` });
await scroller.evaluate((element) => element.scrollTo(0, element.scrollHeight));
await page.waitForTimeout(400);
await page.screenshot({ path: `${OUT}/chat-bottom.png` });
await page.getByRole("button", { name: "View recommendation" }).first().click();
await page.waitForTimeout(600);
await page.screenshot({ path: `${OUT}/product-modal.png` });
console.log("screenshots written to", OUT);
await browser.close();
