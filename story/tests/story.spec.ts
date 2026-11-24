import {test,expect} from "@playwright/test";
test("all real chapters render, evidence is accessible, and the breakdown is intact",async({page})=>{
 const errors:string[]=[];page.on("pageerror",e=>errors.push(String(e)));
 await page.goto("/");
 await expect(page.locator("section[data-chapter]")).toHaveCount(13);
 await expect(page.getByRole("button",{name:/ENTER THE LEDGER/})).toBeVisible();
 await page.locator(".nav-chapter").nth(6).click();
 await expect(page.locator(".chapter-6 .section-heading h2")).toContainText("model fumbled");
 const number=await page.locator(".chapter-6 .huge-score").innerText();
 expect(number).toMatch(/^0\./);
 await page.locator("#time-scrub").focus();
 await page.keyboard.press("ArrowRight");
 await page.keyboard.press("ArrowRight");
 await page.keyboard.press("ArrowRight");
 await expect(page.locator(".chapter-6 .huge-score")).toHaveText("0.0265");
 expect(errors).toEqual([]);
});
test("theme, evidence vault, play/read and keyboard affordances",async({page})=>{
 await page.goto("/");
 await page.locator(".radio-button").click();
 await page.locator(".radio-popup button").filter({hasText:"Acid"}).click();
 await expect(page.locator(".neon-ledger")).toHaveAttribute("data-theme","acid");
 await page.getByRole("button",{name:"Show evidence vault"}).click();
 await expect(page.getByRole("dialog",{name:"Evidence vault"})).toBeVisible();
 await page.keyboard.press("Escape");
 await expect(page.getByRole("dialog",{name:"Evidence vault"})).toHaveCount(0);
 await page.getByRole("button",{name:/Play mode/}).click();
 await expect(page.locator(".neon-ledger")).toHaveClass(/mode-read/);
});
test("responsive navigation and reduced-motion setting",async({page})=>{
 await page.setViewportSize({width:390,height:844});
 await page.emulateMedia({reducedMotion:"reduce"});
 await page.goto("/");
 await page.getByRole("button",{name:"Open chapter navigation"}).click();
 await expect(page.locator(".chapter-nav")).toHaveClass(/open/);
 await expect(page.locator(".vortex-background")).toBeHidden();
});
