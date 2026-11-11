import { chromium } from "@playwright/test";

const BASE = process.env.FRONTEND_URL ?? "http://localhost:3000";
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });

await page.goto(BASE, { waitUntil: "networkidle" });
await page
  .locator("main")
  .getByRole("button", { name: /我想买一瓶沐浴露/ })
  .first()
  .click();
await page
  .getByRole("button", { name: "View recommendation" })
  .first()
  .waitFor({ timeout: 60000 });

await page.getByRole("button", { name: "View recommendation" }).first().click();
await page.getByRole("button", { name: "Place demo order" }).click();
const address = page.getByPlaceholder("Enter a demo address");
await address.fill("1 Demo Road, Shanghai");
await page.getByRole("button", { name: "Confirm demo order" }).click();
await page.waitForSelector("text=Demo order created", { timeout: 15000 });
await page.screenshot({ path: "../docs/assets/order-success.png" });
console.log("order flow ok");

await page.getByRole("button", { name: "Done" }).click();
await page.locator("header").getByRole("button", { name: "Orders" }).click();
const dialog = page.getByRole("dialog");
await dialog.getByText("My orders").waitFor({ timeout: 15000 });
await dialog
  .locator("button")
  .filter({ hasText: "SW-" })
  .first()
  .click();
await dialog.getByText("Order details").waitFor({ timeout: 15000 });
await dialog.getByText("Shipping address").waitFor();
await page
  .getByText(/Demo order .* created/)
  .waitFor({ state: "hidden", timeout: 10000 });
await page.screenshot({ path: "../docs/assets/orders.png" });
console.log("orders UI ok");

await dialog.getByRole("button", { name: "Write a review" }).click();
await page
  .getByPlaceholder("Write your experience…")
  .fill(
    "Used it for two weeks. It cleans well and reduces dandruff, and the scent is light. The bottle pump is a bit stiff.",
  );
await page.getByRole("button", { name: "Submit review" }).click();
await page.getByText("Review submitted").waitFor({ timeout: 60000 });
await page.screenshot({ path: "../docs/assets/review-success.png" });
await page.getByRole("button", { name: "Done" }).click();
await dialog.getByText("Last updated").waitFor({ timeout: 15000 });
console.log("review flow ok");

await dialog.getByRole("button", { name: "Edit review" }).click();
await page.getByRole("button", { name: "Rating 4" }).click();
await page
  .getByPlaceholder("Write your experience…")
  .fill(
    "Used it for a month. Still reduces dandruff, light scent, but the pump is still stiff.",
  );
await page.getByRole("button", { name: "Save changes" }).click();
await page.getByText("Review updated").waitFor({ timeout: 60000 });
await page.getByRole("button", { name: "Done" }).click();
await dialog.getByText("Last updated").waitFor({ timeout: 15000 });
await page.screenshot({ path: "../docs/assets/review-detail.png" });
console.log("review edit ok");

await dialog.getByRole("button", { name: "Close" }).last().click();
await page.getByRole("button", { name: "New shopping chat" }).click();
await page.locator("aside li button").first().click();
await page
  .getByRole("button", { name: "View recommendation" })
  .first()
  .waitFor({ timeout: 15000 });
console.log("history replay ok");

await page.locator("header").getByRole("button", { name: "Sell" }).click();
const sellerDialog = page.getByRole("dialog");
await sellerDialog.getByText("List a product").waitFor({ timeout: 15000 });
await sellerDialog
  .getByPlaceholder(/For example: a 500ml amino-acid body wash/)
  .fill(
    "Demo Shop anti-dandruff shampoo, 400ml, for oily scalps, reduces dandruff, fresh scent, ¥59. The pump is a little stiff.",
  );
await sellerDialog.locator('input[type="number"]').fill("59");
await sellerDialog.locator("select").selectOption("洗发水");
await sellerDialog
  .getByPlaceholder("Independent seller / your brand")
  .fill("Demo Shop");
await sellerDialog
  .getByRole("button", { name: "Let the agent structure and publish" })
  .click();
await sellerDialog.getByText("Listing created").waitFor({ timeout: 60000 });
await page.screenshot({ path: "../docs/assets/seller-success.png" });
await sellerDialog.getByRole("button", { name: "Done" }).click();
console.log("seller flow ok");

await page.getByRole("button", { name: "New shopping chat" }).click();
await page
  .getByPlaceholder(/Tell me what you want to buy/)
  .fill("帮我找一款适合敏感肌的沐浴露，100 元以内，合适的话我想买两瓶。");
await page.getByRole("button", { name: "Send" }).click();
await page
  .getByText("Pending confirmation", { exact: true })
  .waitFor({ timeout: 120000 });
await page.screenshot({ path: "../docs/assets/agent-plan.png" });
await page.getByRole("button", { name: "Confirm and run" }).click();
await page.getByText("Completed", { exact: true }).waitFor({ timeout: 120000 });
await page.screenshot({ path: "../docs/assets/agent-success.png" });
console.log("chat agent flow ok");

await page.getByRole("button", { name: "New shopping chat" }).click();
await page
  .getByPlaceholder(/Tell me what you want to buy/)
  .fill(
    "帮我找京东和淘宝上 100 元以内的护肤霜，比较价格和评价后推荐三款性价比最高的。",
  );
await page.getByRole("button", { name: "Send" }).click();
const mcpCardTitle = page.getByText("MCP marketplace comparison", {
  exact: true,
});
await mcpCardTitle.waitFor({ timeout: 180000 });
await page.getByText("MCP tool calls", { exact: true }).waitFor();
await page
  .locator("code")
  .filter({ hasText: "search_taobao_products" })
  .first()
  .waitFor();
await mcpCardTitle.scrollIntoViewIfNeeded();
await page.waitForTimeout(300);
await page.screenshot({ path: "../docs/assets/mcp-compare.png" });
console.log("mcp compare flow ok");

await page
  .locator("header")
  .getByRole("button", { name: "MCP", exact: true })
  .click();
const mcpDialog = page.getByRole("dialog");
await mcpDialog.getByText("MCP external tools", { exact: true }).waitFor();
await mcpDialog.getByText("search_jd_products", { exact: true }).waitFor();
await page.screenshot({ path: "../docs/assets/mcp-tools.png" });
await mcpDialog.getByRole("button", { name: "Close" }).click();
console.log("mcp tools modal ok");

await page.getByRole("button", { name: "New shopping chat" }).click();
await page.waitForTimeout(1200);
await page.locator("aside li button").first().click();
await page
  .getByText("MCP marketplace comparison", { exact: true })
  .waitFor({ timeout: 20000 });
console.log("mcp history replay ok");

await browser.close();
