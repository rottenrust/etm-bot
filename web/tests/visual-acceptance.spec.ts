import { createHmac } from "node:crypto";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { expect, test, type Browser, type Page, type Route } from "@playwright/test";

const evidenceDir = process.env.KOTIK_EVIDENCE_DIR || "test-results/screenshots";
const telegramSdkPath = process.env.KOTIK_TELEGRAM_SDK_PATH;
const today = "2026-05-10";
const syntheticToken = "123456:synthetic-mini-app-browser-token";
const todayAt = (day: string, time: string) => `${day}T${time}:00+03:00`;
const addIsoDays = (day: string, offset: number) => {
  const value = new Date(`${day}T00:00:00Z`);
  value.setUTCDate(value.getUTCDate() + offset);
  return value.toISOString().slice(0, 10);
};
const clockInstalled = new WeakSet<Page>();
const resourceLoggingInstalled = new WeakSet<Page>();

type FixtureTask = {
  id: number;
  text: string;
  deadline: string | null;
  deadlineTime: string | null;
  listId: string;
  listTitle: string;
  note: string | null;
  recurrence: string | null;
  snoozedUntil: string | null;
  reminderEnabled: boolean;
  completedAt: string | null;
};

const fixtureTasks: FixtureTask[] = [
  task(1, "Созвон", "2026-05-09", "18:30", "work", "Работа"),
  task(2, "Йога", today, "10:30", "health", "Здоровье"),
  task(3, "Приборка", today, "12:30", "home", "Дом"),
  task(4, "Тренировка", today, null, "general", "Общий", { completedAt: todayAt(today, "08:20") }),
  task(5, "Лейка для душа", today, "19:30", "shopping", "Покупки"),
  task(6, "Заварить чай", "2026-05-11", "09:00", "general", "Общий"),
  task(7, "Молоко", "2026-05-11", null, "shopping", "Покупки"),
  task(8, "Покормить кота", "2026-05-11", "13:30", "general", "Общий"),
];

const editFixtureTask = task(99, "Тренировка", today, "16:00", "health", "Здоровье", { note: "Бёдра и ягодицы", reminderEnabled: false });
const listFixtureTasks = [
  task(91, "Турнички", today, "08:30", "health", "Здоровье"),
  task(92, "Тренировка", today, "18:30", "health", "Здоровье"),
];

function task(
  id: number,
  text: string,
  deadline: string | null,
  deadlineTime: string | null,
  listId: string,
  listTitle: string,
  extra: Partial<FixtureTask> = {},
): FixtureTask {
  return {
    id,
    text,
    deadline,
    deadlineTime,
    listId,
    listTitle,
    note: null,
    recurrence: null,
    snoozedUntil: null,
    reminderEnabled: false,
    completedAt: null,
    ...extra,
  };
}

const categories = [
  { id: "general", title: "Общее", count: 4, tasks: [] },
  { id: "health", title: "Здоровье", count: 2, tasks: listFixtureTasks },
  { id: "shopping", title: "Покупки", count: 3, tasks: [] },
  { id: "work", title: "Работа", count: 2, tasks: [] },
  { id: "home", title: "Дом", count: 2, tasks: [] },
];

test.beforeAll(async () => {
  await mkdir(evidenceDir, { recursive: true });
});

test("renders and captures the 21 interface states", async ({ page }) => {
  await page.setViewportSize({ width: 402, height: 874 });
  await setupPage(page, false);

  await expect(page.getByText("Просрочено", { exact: true }).first()).toBeVisible();
  await capture(page, "home-nearest-populated");

  await page.getByRole("button", { name: "Что дальше?" }).click();
  await expect(page.locator(".calendar-strip button")).toHaveCount(31);
  await expect.poll(() => page.locator(".calendar-strip button").evaluateAll((buttons) => buttons.slice(0, 7).map((button) => button.querySelector("span")?.textContent))).toEqual(["Вт", "Ср", "Чт", "Пт", "Сб", "Вс", "Пн"]);
  await expect(page.locator(".calendar-strip button i.has-tasks")).toHaveCount(5);
  await capture(page, "home-calendar-populated");

  await setupPage(page, true);
  await page.getByRole("button", { name: "Что дальше?" }).click();
  await page.getByRole("button", { name: "Ср 11" }).click();
  await capture(page, "home-calendar-empty");
  await page.getByRole("button", { name: "Ближайшие задачи" }).click();
  await capture(page, "home-nearest-empty");

  const taskState = await setupPage(page, false);
  taskState.tasks.push({ ...editFixtureTask });
  await page.clock.runFor(5000);
  await openTask(page, "Тренировка", "Здоровье");
  await capture(page, "task-read-only");
  await page.locator(".task-form-screen > .primary-button").click();
  await page.getByRole("button", { name: "Завтра" }).click();
  await page.locator("#task-time").fill("18:00");
  await page.locator("#task-note").fill("Руки и корпус");
  await capture(page, "task-edit");
  await page.getByRole("button", { name: "Удалить дело" }).click();
  await expect(page.getByRole("dialog", { name: "Вы уверенны?" })).toBeVisible();
  await capture(page, "task-delete-confirm");

  await setupPage(page, false);
  await page.locator(".footer-cat-button").click();
  await capture(page, "task-add-empty");

  await setupPage(page, false);
  await page.locator(".footer-cat-button").click();
  await page.locator("#task-text").fill("Тренировка");
  await page.getByRole("button", { name: "Сегодня" }).click();
  await page.locator("#task-time").fill("16:00");
  await page.locator("#task-note").fill("Бёдра и ягодицы");
  await page.locator(".category-current").click();
  await page.locator(".category-option").filter({ hasText: "Здоровье" }).click();
  await expect(page.getByRole("button", { name: "Добавить задачу" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Напомнить" })).toHaveAttribute("aria-pressed", "false");
  await capture(page, "task-reminder-off");
  await page.getByRole("button", { name: "Напомнить" }).click();
  await expect(page.getByRole("button", { name: "Напомнить" })).toHaveAttribute("aria-pressed", "true");
  await capture(page, "task-reminder-on");

  await setupPage(page, false);
  await page.locator(".footer-cat-button").click();
  await expect(page.locator(".category-option")).toHaveCount(0);
  await page.locator(".category-current").click();
  await expect(page.locator(".category-option").first()).toBeVisible();
  await capture(page, "task-category-dropdown");

  const listsState = await setupPage(page, false);
  listsState.listTasks = listFixtureTasks.map((item) => ({ ...item }));
  listsState.categoryCounts = { general: 4, health: 2, shopping: 3, work: 2, home: 2 };
  await page.getByRole("button", { name: /Списки/ }).click();
  await expect(page.locator(".lists-screen")).toBeVisible();
  await expect(page.locator(".category-accordion > .accordion-heading > strong").evaluateAll((names) => names.map((name) => name.textContent))).resolves.toEqual(["Общее", "Здоровье", "Дом", "Покупки", "Работа"]);
  await capture(page, "lists-collapsed");
  await page.getByRole("button", { name: /Здоровье/ }).first().click();
  await capture(page, "lists-expanded");

  await setupPage(page, false);
  await page.getByRole("button", { name: /Семья/ }).click();
  await expect(page.locator(".family-screen")).toBeVisible();
  await capture(page, "family");
  await page.getByRole("button", { name: "Удалить Ира" }).click();
  await capture(page, "family-remove-confirm");

  await setupPage(page, false);
  await page.getByRole("button", { name: /Нужна помощь/ }).click();
  await capture(page, "help");

  const onboardingContext = await page.context().browser()?.newContext({ viewport: { width: 402, height: 874 } });
  if (!onboardingContext) throw new Error("Browser context is unavailable");
  const onboardingPage = await onboardingContext.newPage();
  await setupPage(onboardingPage, false, true);
  await capture(onboardingPage, "onboarding-welcome");
  await onboardingPage.setViewportSize({ width: 410, height: 874 });
  await onboardingPage.getByRole("button", { name: "Обучение" }).click();
  await capture(onboardingPage, "onboarding-step-1");
  await onboardingPage.getByRole("button", { name: /Дальше/ }).click();
  await capture(onboardingPage, "onboarding-step-2");
  await onboardingPage.getByRole("button", { name: /Дальше/ }).click();
  await capture(onboardingPage, "onboarding-step-3");
  await onboardingPage.getByRole("button", { name: /Дальше/ }).click();
  await capture(onboardingPage, "onboarding-step-4");
  await onboardingContext.close();
});

test("creates and edits tasks, returns to the opened list after save and delete, and keeps onboarding choice", async ({ page }) => {
  const state = await setupPage(page, false);
  await page.locator(".footer-cat-button").click();
  await page.locator("#task-text").fill("Новая задача");
  await page.getByRole("button", { name: "Добавить задачу" }).click();
  await expect(page.getByText("Новая задача", { exact: true })).toBeVisible();

  await openTask(page, "Новая задача");
  await page.locator(".task-form-screen > .primary-button").click();
  await page.locator("#task-text").fill("Обновлённая задача");
  await page.getByRole("button", { name: "Сохранить изменения" }).click();
  await expect(page.getByText("Обновлённая задача", { exact: true })).toBeVisible();

  state.listTasks = listFixtureTasks.map((item) => ({ ...item }));
  state.categoryCounts = { general: 4, health: 2, shopping: 3, work: 2, home: 2 };
  await page.getByRole("button", { name: /Списки/ }).click();
  await page.getByRole("button", { name: /Здоровье/ }).first().click();
  await openTask(page, "Турнички", "Здоровье");
  await page.locator(".task-form-screen > .primary-button").click();
  await page.locator("#task-text").fill("Турнички изменены");
  await page.getByRole("button", { name: "Сохранить изменения" }).click();
  await expect(page.locator(".lists-screen")).toBeVisible();
  await expect(page.getByRole("button", { name: /Здоровье/ }).first()).toHaveAttribute("aria-expanded", "true");
  await expect(page.getByText("Турнички изменены", { exact: true })).toBeVisible();
  await openTask(page, "Турнички изменены", "Здоровье");
  await page.locator(".task-form-screen > .primary-button").click();
  await page.getByRole("button", { name: "Удалить дело" }).click();
  await page.getByRole("dialog", { name: "Вы уверенны?" }).getByRole("button", { name: "Да" }).click();
  await expect(page.locator(".lists-screen")).toBeVisible();
  await expect(page.getByRole("button", { name: /Здоровье/ }).first()).toHaveAttribute("aria-expanded", "true");
  await expect(page.getByText("Турнички изменены", { exact: true })).toHaveCount(0);

  const onboardingContext = await page.context().browser()?.newContext({ viewport: { width: 410, height: 874 } });
  if (!onboardingContext) throw new Error("Browser context is unavailable");
  const onboardingPage = await onboardingContext.newPage();
  await setupPage(onboardingPage, false, true);
  await onboardingPage.getByRole("button", { name: "Пропустить" }).click();
  await expect(onboardingPage.getByRole("button", { name: "Что дальше?" })).toBeVisible();
  await onboardingPage.reload();
  await expect(onboardingPage.getByRole("button", { name: "Что дальше?" })).toBeVisible();
  await onboardingContext.close();
});

test("refreshes shared changes without overwriting a draft; removes deleted data and revoked family", async ({ page }) => {
  const state = await setupPage(page, false);
  await openTask(page, "Созвон", "Работа");
  state.tasks[0].text = "Обновил другой участник";
  await page.clock.runFor(5000);
  await expect(page.locator(".task-name-control > span")).toHaveText("Обновил другой участник");

  await page.locator(".task-form-screen > .primary-button").click();
  await page.locator("#task-text").fill("Мой несохранённый ввод");
  state.tasks[0].text = "Второе внешнее изменение";
  await page.clock.runFor(5000);
  await expect(page.locator("#task-text")).toHaveValue("Мой несохранённый ввод");

  state.tasks.splice(0, 1);
  await page.clock.runFor(5000);
  await expect(page.getByRole("button", { name: "Ближайшие задачи" })).toBeVisible();
  await expect(page.getByText("Второе внешнее изменение", { exact: true })).toHaveCount(0);

  await page.getByRole("button", { name: /Семья/ }).click();
  await expect(page.locator(".family-screen")).toBeVisible();
  state.hasFamily = false;
  await page.clock.runFor(5000);
  await expect(page.getByRole("link", { name: "Открыть бот" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Открыть бот" })).toHaveAttribute("href", "https://t.me/easy_task_manager_bot");
});

test("fits narrow, standard, and desktop widths and accepts keyboard input while scrolling", async ({ page }) => {
  await setupPage(page, false);
  for (const width of [320, 390, 402, 1280]) {
    await page.setViewportSize({ width, height: 700 });
    const widthInfo = await page.evaluate(() => ({
      content: document.documentElement.scrollWidth,
      viewport: window.innerWidth,
    }));
    expect(widthInfo.content, `horizontal overflow at ${width}px`).toBeLessThanOrEqual(widthInfo.viewport);
    const clipped = await page.locator(".shortcut span").evaluateAll((labels) =>
      labels.filter((label) => label.scrollWidth > label.clientWidth).map((label) => label.textContent)
    );
    expect(clipped, `clipped shortcut labels at ${width}px`).toEqual([]);
    if (width === 320 || width === 1280) await capture(page, `home-${width}px`);
  }

  await page.setViewportSize({ width: 320, height: 640 });
  await page.locator(".footer-cat-button").click();
  const input = page.locator("#task-text");
  await input.focus();
  await page.keyboard.type("Клавиатурный ввод");
  await expect(input).toHaveValue("Клавиатурный ввод");
  expect(await page.evaluate(() => document.documentElement.scrollHeight)).toBeGreaterThan(640);
  await page.keyboard.press("Tab");
  await expect(page.locator(":focus")).toHaveClass(/date-choice/);
});

test("keeps onboarding artwork and controls inside the card on a narrow screen", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 640 });
  await setupPage(page, false, true);
  await page.getByRole("button", { name: "Обучение", exact: true }).click();
  for (let step = 1; step <= 4; step++) {
    const bounds = await page.locator(".onboarding-card").evaluate((card) => {
      const rect = card.getBoundingClientRect();
      const footer = card.querySelector("footer")!.getBoundingClientRect();
      const artwork = card.querySelector(".onboarding-artwork")!.getBoundingClientRect();
      return { left: rect.left, right: rect.right, bottom: rect.bottom, footerLeft: footer.left, footerRight: footer.right, footerBottom: footer.bottom, artworkRight: artwork.right, viewport: window.innerWidth };
    });
    expect(bounds.left, `card left on step ${step}`).toBeGreaterThanOrEqual(0);
    expect(bounds.right, `card right on step ${step}`).toBeLessThanOrEqual(bounds.viewport);
    expect(bounds.artworkRight, `artwork on step ${step}`).toBeLessThanOrEqual(bounds.right);
    expect(bounds.footerLeft).toBeGreaterThanOrEqual(bounds.left);
    expect(bounds.footerRight).toBeLessThanOrEqual(bounds.right);
    expect(bounds.footerBottom, `controls on step ${step}`).toBeLessThanOrEqual(bounds.bottom);
    if (step < 4) await page.getByRole("button", { name: /Дальше/ }).click();
  }
  await page.getByRole("button", { name: "Начать" }).click();
  await expect(page.getByRole("button", { name: "Ближайшие задачи" })).toBeVisible();
});

test("shows an invitation code without a bot link and confirms only a successful copy", async ({ page }) => {
  const state = await setupPage(page, false);
  await page.getByRole("button", { name: /Семья/ }).click();
  state.inviteLink = null;
  await page.getByRole("button", { name: /Пригласить в семью/ }).click();
  await expect(page.locator(".invite-box small")).toHaveText("Код приглашения: ABC12345");
  await expect(page.getByText("Ссылка скопирована", { exact: true })).toHaveCount(0);

  await page.context().grantPermissions(["clipboard-read", "clipboard-write"]);
  state.inviteLink = "https://t.me/easy_task_manager_bot?start=ABC12345";
  await page.getByRole("button", { name: /Ссылка для приглашения/ }).click();
  await expect(page.getByText("Ссылка скопирована", { exact: true })).toBeVisible();
  await expect.poll(() => page.evaluate(() => navigator.clipboard.readText())).toBe(state.inviteLink);
});

test("scrolls to a later calendar date and selects it without losing the selection", async ({ page }) => {
  const state = await setupPage(page, false);
  await page.getByRole("button", { name: "Что дальше?" }).click();
  const strip = page.locator(".calendar-strip");
  await expect(strip.locator("button")).toHaveCount(31);
  await strip.evaluate((element) => { element.scrollLeft = element.scrollWidth; });
  const lastDay = strip.locator("button").last();
  const laterDate = addIsoDays(today, 30);
  const laterLabel = await lastDay.getAttribute("aria-label");
  await lastDay.click();
  await expect(strip.locator("button.selected")).toHaveAttribute("aria-label", laterLabel || "");
  expect(state.calendarSelected).toBe(laterDate);
  expect(state.calendarStart).toBe(addIsoDays(laterDate, -15));
  await expect(strip.locator("button")).toHaveCount(31);
  const selectedBounds = await strip.evaluate((element) => {
    const stripBounds = element.getBoundingClientRect();
    const selectedBounds = element.querySelector("button.selected")?.getBoundingClientRect();
    return selectedBounds ? { left: selectedBounds.left - stripBounds.left, right: selectedBounds.right - stripBounds.left, width: stripBounds.width } : null;
  });
  expect(selectedBounds).not.toBeNull();
  expect(selectedBounds!.left).toBeGreaterThanOrEqual(0);
  expect(selectedBounds!.right).toBeLessThanOrEqual(selectedBounds!.width);
  expect(await strip.evaluate((element) => element.scrollWidth > element.clientWidth)).toBe(true);
});

test("opens the native date picker on desktop and mobile and exposes a usable fallback", async ({ browser }) => {
  const scenarios = [
    { viewport: { width: 1280, height: 900 }, isMobile: false, fallback: false },
    { viewport: { width: 390, height: 844 }, isMobile: true, fallback: false },
    { viewport: { width: 390, height: 844 }, isMobile: true, fallback: true },
  ];
  for (const scenario of scenarios) {
    const context = await browser.newContext({ viewport: scenario.viewport, isMobile: scenario.isMobile, hasTouch: scenario.isMobile });
    const page = await context.newPage();
    await page.addInitScript((fallback) => {
      if (fallback) {
        Object.defineProperty(HTMLInputElement.prototype, "showPicker", { configurable: true, value: undefined });
        return;
      }
      const showPicker = HTMLInputElement.prototype.showPicker;
      if (showPicker) {
        HTMLInputElement.prototype.showPicker = function () {
          this.dataset.pickerOpened = "true";
          return showPicker.call(this);
        };
      }
    }, scenario.fallback);
    await setupPage(page, false);
    await page.locator(".footer-cat-button").click();
    await page.getByRole("button", { name: "Другая дата" }).click();
    const dateInput = page.locator('input[type="date"][aria-label="Выберите дату"]');
    if (scenario.fallback) {
      await expect(dateInput).toBeVisible();
      await dateInput.fill("2026-05-20");
      await expect(dateInput).toHaveValue("2026-05-20");
    } else {
      await expect.poll(() => dateInput.getAttribute("data-picker-opened")).toBe("true");
    }
    await context.close();
  }
});

test("accepts mobile time entry digit by digit and sends normalized create and edit payloads", async ({ browser }) => {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
  const page = await context.newPage();
  const created = await setupPage(page, false);
  await page.locator(".footer-cat-button").tap();
  await page.locator("#task-text").fill("Новая задача");
  const timeInput = page.locator("#task-time");
  await expect(timeInput).toHaveAttribute("type", "text");
  await expect(timeInput).toHaveAttribute("inputmode", "numeric");
  await page.locator(".time-control > img").tap();
  await expect(timeInput).toBeFocused();
  await timeInput.pressSequentially("1830");
  await expect(timeInput).toHaveValue("1830");
  await timeInput.blur();
  await expect(timeInput).toHaveValue("18:30");
  const timeRow = page.locator(".time-control");
  const rowBounds = await timeRow.boundingBox();
  expect(rowBounds).not.toBeNull();
  for (const x of [2, rowBounds!.width - 2]) {
    await timeRow.tap({ position: { x, y: rowBounds!.height / 2 } });
    await expect(timeInput).toBeFocused();
    await timeInput.blur();
  }
  await page.screenshot({ path: path.join(evidenceDir, "mobile-time-entry-18-30.png"), fullPage: false, animations: "disabled" });
  await page.getByRole("button", { name: "Добавить задачу" }).tap();
  await expect.poll(() => created.lastTaskPayload).toEqual({
    text: "Новая задача",
    deadline: today,
    deadlineTime: "18:30",
    listId: "general",
    note: null,
    reminderEnabled: false,
  });

  const editPage = await context.newPage();
  const edited = await setupPage(editPage, false);
  edited.tasks.push({ ...editFixtureTask });
  await editPage.clock.runFor(5000);
  await openTask(editPage, "Тренировка", "Здоровье");
  await editPage.locator(".task-form-screen > .primary-button").tap();
  const editTime = editPage.locator("#task-time");
  await editTime.tap();
  await editTime.fill("");
  await editTime.pressSequentially("0745");
  await editTime.blur();
  await expect(editTime).toHaveValue("07:45");
  await editPage.getByRole("button", { name: "Сохранить изменения" }).tap();
  await expect.poll(() => edited.lastTaskPayload).toEqual({
    text: "Тренировка",
    deadline: today,
    deadlineTime: "07:45",
    listId: "health",
    note: "Бёдра и ягодицы",
    reminderEnabled: false,
  });
  await context.close();
});

test("rejects invalid time without an API write and allows an empty time", async ({ page }) => {
  const state = await setupPage(page, false);
  await page.locator(".footer-cat-button").click();
  await page.locator("#task-text").fill("Дело без времени");
  const timeInput = page.locator("#task-time");
  for (const invalidTime of ["25:30", "18:60"]) {
    await timeInput.fill(invalidTime);
    await timeInput.blur();
    await expect(timeInput).toHaveAttribute("aria-invalid", "true");
    await expect(page.getByRole("alert")).toHaveText("Введите время от 00:00 до 23:59.");
  }
  await page.getByRole("button", { name: "Добавить задачу" }).click();
  expect(state.lastTaskPayload).toBeUndefined();

  await page.getByRole("button", { name: "Без дедлайна" }).click();
  await expect(timeInput).toHaveValue("");
  await page.getByRole("button", { name: "Добавить задачу" }).click();
  await expect.poll(() => state.lastTaskPayload).toEqual({
    text: "Дело без времени",
    deadline: null,
    deadlineTime: null,
    listId: "general",
    note: null,
    reminderEnabled: false,
  });
});

type MockState = { tasks: FixtureTask[]; hasFamily: boolean; inviteLink?: string | null; listTasks?: FixtureTask[]; categoryCounts?: Record<string, number>; todayStat?: number; calendarSelected?: string; calendarStart?: string; lastTaskPayload?: Record<string, unknown> };

async function setupPage(page: Page, empty: boolean, onboarding = false): Promise<MockState> {
  if (!resourceLoggingInstalled.has(page)) {
    page.on("console", (message) => {
      if (/font|OTS/i.test(message.text())) console.log(`browser font message: ${message.type()} ${message.text()}`);
    });
    page.on("requestfailed", (request) => {
      if (/\.(?:woff2?|ttf)(?:\?|$)/i.test(request.url())) console.log(`font request failed: ${request.url()} (${request.failure()?.errorText})`);
    });
    page.on("response", (response) => {
      if (/\.(?:woff2?|ttf)(?:\?|$)/i.test(response.url())) console.log(`font response: ${response.status()} ${response.url()}`);
    });
    resourceLoggingInstalled.add(page);
  }
  if (!clockInstalled.has(page)) {
    await page.clock.install({ time: new Date("2026-05-10T15:30:00Z") });
    clockInstalled.add(page);
  }
  const initData = signedInitData(101);
  await page.addInitScript(({ initData, showOnboarding }) => {
    if (!showOnboarding) localStorage.setItem("kotik-onboarding-seen", "1");
    const launch = new URLSearchParams(location.hash.slice(1));
    launch.set("tgWebAppData", initData);
    launch.set("tgWebAppVersion", "8.0");
    launch.set("tgWebAppPlatform", "android");
    location.hash = launch.toString();
  }, { initData, showOnboarding: onboarding });
  await page.unrouteAll();
  const state: MockState = { tasks: empty ? [] : fixtureTasks.map((item) => ({ ...item })), hasFamily: true, todayStat: empty ? 0 : 5 };
  if (telegramSdkPath) {
    await page.route(/^https:\/\/telegram\.org\/js\/telegram-web-app\.js\?64$/, (route) => route.fulfill({ path: path.resolve(telegramSdkPath), contentType: "application/javascript" }));
  }
  await page.route("**/api/**", (route) => mockApi(route, state, initData));
  await page.goto("/");
  const launch = await page.evaluate(() => {
    const webApp = (window as Window & { Telegram?: { WebApp?: { initData?: string } } }).Telegram?.WebApp;
    return { initData: webApp?.initData, launchData: new URLSearchParams(location.hash.slice(1)).get("tgWebAppData") };
  });
  expect(launch.initData, "official SDK must read initData from Telegram's launch hash").toBe(initData);
  expect(launch.launchData).toBe(initData);
  if (onboarding) await expect(page.getByRole("heading", { name: "Добро пожаловать!" })).toBeVisible();
  else await expect(page.getByRole("button", { name: "Ближайшие задачи" })).toBeVisible();
  return state;
}

async function mockApi(route: Route, state: MockState, expectedInitData: string) {
  const request = route.request();
  expect(request.headers()["x-telegram-init-data"], "API auth must come from Telegram WebApp.initData").toBe(expectedInitData);
  const url = new URL(request.url());
  const allTasks = state.tasks;
  let body: unknown = {};
  let status = 200;
  if (url.pathname === "/api/me") {
    body = { user: { chatId: 101, name: "Паша" }, hasFamily: state.hasFamily };
  } else if (!state.hasFamily) {
    body = { error: "Family membership required." };
    status = 403;
  } else if (url.pathname === "/api/home") {
    const mode = url.searchParams.get("mode") === "calendar" ? "calendar" : "nearest";
    const selectedDate = url.searchParams.get("date") || today;
    state.calendarSelected = mode === "calendar" ? selectedDate : state.calendarSelected;
    const selectedOffset = Math.round((Date.parse(`${selectedDate}T00:00:00Z`) - Date.parse(`${today}T00:00:00Z`)) / 86_400_000);
    const calendarFirstDate = selectedOffset >= 24 || selectedOffset < 0 ? addIsoDays(selectedDate, -15) : today;
    state.calendarStart = mode === "calendar" ? calendarFirstDate : state.calendarStart;
    const firstDate = mode === "calendar" ? selectedDate : today;
    const nextDate = mode === "calendar" ? addIsoDays(firstDate, 1) : "2026-05-11";
    const sections = [
      section("overdue", "Просрочено", null, "purple", allTasks.filter((item) => item.deadline && item.deadline < today)),
      section(firstDate, "Сегодня", firstDate, "green", allTasks.filter((item) => item.deadline === firstDate)),
      section(nextDate, "Завтра", nextDate, "green", allTasks.filter((item) => item.deadline === nextDate)),
    ];
    if (mode !== "calendar" && allTasks.some((item) => item.deadline === null)) {
      sections.push(section("no-deadline", "Без дедлайна", null, "green", allTasks.filter((item) => item.deadline === null)));
    }
    body = {
      mode,
      today,
      selectedDate,
      stats: { today: state.todayStat ?? allTasks.filter((item) => item.deadline === today && !item.completedAt).length, overdue: allTasks.filter((item) => item.deadline && item.deadline < today && !item.completedAt).length },
      calendar: Array.from({ length: 31 }, (_, index) => {
        const date = addIsoDays(calendarFirstDate, index);
        const dayOffset = Math.round((Date.parse(`${date}T00:00:00Z`) - Date.parse(`${today}T00:00:00Z`)) / 86_400_000);
        return {
          date,
          weekday: ["Вт", "Ср", "Чт", "Пт", "Сб", "Вс", "Пн"][(dayOffset % 7 + 7) % 7],
          day: Number(date.slice(-2)),
          selected: date === selectedDate,
          hasTasks: dayOffset >= 0 && dayOffset < 7 ? [0, 3, 4, 5, 6].includes(dayOffset) : allTasks.some((item) => item.deadline === date),
        };
      }),
      sections,
    };
  } else if (url.pathname === "/api/lists") {
    const listTasks = state.listTasks ?? allTasks;
    body = { categories: categories.map((category) => ({ ...category, count: state.categoryCounts?.[category.id] ?? listTasks.filter((item) => item.listId === category.id && !item.completedAt).length, tasks: listTasks.filter((item) => item.listId === category.id) })), missingPresets: [{ id: "dacha", title: "Дача" }, { id: "vacation", title: "Отпуск" }], presets: [] };
  } else if (url.pathname === "/api/family") {
    body = { ownerChatId: 101, canManageMembers: true, members: [{ chatId: 101, name: "Паша" }, { chatId: 102, name: "Ира" }, { chatId: 103, name: "Блинчик" }] };
  } else if (url.pathname === "/api/family/invite") {
    body = { code: "ABC12345", botLink: state.inviteLink === undefined ? "https://t.me/easy_task_manager_bot?start=ABC12345" : state.inviteLink };
  } else if (url.pathname === "/api/tasks" && request.method() === "POST") {
    const payload = request.postDataJSON() as Record<string, unknown>;
    state.lastTaskPayload = payload;
    const createdTask = task(99, String(payload.text), payload.deadline as string | null, payload.deadlineTime as string | null, String(payload.listId), "Общий", { note: payload.note as string | null, reminderEnabled: Boolean(payload.reminderEnabled) });
    allTasks.push(createdTask);
    body = { task: createdTask };
    status = 201;
  } else if (url.pathname.startsWith("/api/tasks/") && request.method() === "PATCH") {
    const id = Number(url.pathname.split("/")[3]);
    const payload = request.postDataJSON() as Record<string, unknown>;
    state.lastTaskPayload = payload;
    const item = [...allTasks, ...(state.listTasks ?? [])].find((candidate) => candidate.id === id);
    if (item) item.text = String(payload.text || item.text);
    body = { task: item ?? task(99, String(payload.text || "Обновлённая задача"), today, null, "general", "Общий") };
  } else if (url.pathname.startsWith("/api/tasks/") && request.method() === "DELETE") {
    const id = Number(url.pathname.split("/")[3]);
    const index = allTasks.findIndex((candidate) => candidate.id === id);
    if (index >= 0) allTasks.splice(index, 1);
    if (state.listTasks) state.listTasks = state.listTasks.filter((candidate) => candidate.id !== id);
    body = { deleted: true };
  } else if (url.pathname.startsWith("/api/tasks/") && request.method() === "POST") {
    const id = Number(url.pathname.split("/")[3]);
    const item = [...allTasks, ...(state.listTasks ?? [])].find((candidate) => candidate.id === id) ?? allTasks[0];
    if (item) item.completedAt = todayAt(today, "09:01");
    body = { task: item, changed: true };
  }
  await route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
}

function section(id: string, title: string, date: string | null, tone: "green" | "purple", tasks: FixtureTask[]) {
  return { id, title, date, tone, tasks };
}

async function openTask(page: Page, title: string, category?: string) {
  let locator = page.locator(".task-card-body").filter({ hasText: title });
  if (category) locator = locator.filter({ hasText: category });
  await locator.click();
  await expect(page.locator(".task-form-screen > .primary-button")).toBeVisible();
}

async function capture(page: Page, scenario: string) {
  const statuses = await page.evaluate(async () => {
    const faces = await document.fonts.load('500 22px "Inter"', "Котик");
    await document.fonts.ready;
    return faces.map((face) => face.status);
  });
  expect(statuses).toEqual(["loaded"]);
  await page.evaluate(() => {
    if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
  });
  await page.screenshot({ path: path.join(evidenceDir, `${scenario}.png`), fullPage: false, animations: "disabled" });
}

function signedInitData(chatId: number) {
  const params = new URLSearchParams({
    auth_date: String(Math.floor(Date.now() / 1000)),
    user: JSON.stringify({ id: chatId, first_name: "Тест" }),
  });
  const dataCheckString = [...params.entries()].sort(([a], [b]) => a.localeCompare(b)).map(([key, value]) => `${key}=${value}`).join("\n");
  const secretKey = createHmac("sha256", "WebAppData").update(syntheticToken).digest();
  params.set("hash", createHmac("sha256", secretKey).update(dataCheckString).digest("hex"));
  return params.toString();
}
