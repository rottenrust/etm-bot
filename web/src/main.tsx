import { createRoot } from "react-dom/client";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import backIcon from "./assets/figma/back.svg";
import bellIcon from "./assets/figma/form-bell.svg";
import pencilIcon from "./assets/figma/form-pencil.svg";
import timeIcon from "./assets/figma/form-time.svg";
import homeGeneralIcon from "./assets/figma/home-general.svg";
import homeIcon from "./assets/figma/category-home.svg";
import healthIcon from "./assets/figma/category-health.svg";
import shoppingIcon from "./assets/figma/category-shopping.svg";
import workIcon from "./assets/figma/category-work.svg";
import dropdownIcon from "./assets/figma/dropdown.svg";
import helpIcon from "./assets/figma/help.svg";
import shortcutArrow from "./assets/figma/shortcut-arrow.svg";
import statClockIcon from "./assets/figma/stat-clock.svg";
import statOverdueIcon from "./assets/figma/stat-overdue.svg";
import statNoOverdueIcon from "./assets/figma/stat-no-overdue.svg";
import taskCheckEmptyIcon from "./assets/figma/task-check-empty.svg";
import taskCheckOverdueIcon from "./assets/figma/task-check-overdue.svg";
import taskCheckDoneIcon from "./assets/figma/task-check-done.svg";
import inviteLinkIcon from "./assets/figma/family-invite-link.svg";
import creatorStarIcon from "./assets/figma/family-owner-star.svg";
import memberTrashIcon from "./assets/figma/family-member-delete.svg";
import listAddIcon from "./assets/figma/list-add.svg";
import dialogSprigIcon from "./assets/figma/dialog-sprig.svg";
import footerBranchFarRight from "./assets/figma/home-foot-branch-far-right.svg";
import onboardingArrow1 from "./assets/figma/onboarding-arrow-1.svg";
import onboardingArrow2 from "./assets/figma/onboarding-arrow-2.svg";
import onboardingArrow3 from "./assets/figma/onboarding-arrow-3.svg";
import onboardingDateCalendar from "./assets/figma/onboarding-date-calendar.svg";
import onboardingDateDotPurple from "./assets/figma/onboarding-date-dot-purple.svg";
import onboardingDateDotGreen from "./assets/figma/onboarding-date-dot-green.svg";
import onboardingTimeClock from "./assets/figma/onboarding-time-clock.svg";
import onboardingToggle from "./assets/figma/onboarding-toggle.svg";
import onboardingCategoryArrow from "./assets/figma/onboarding-category-arrow.svg";
import helpListIcon from "./assets/figma/help-list.png";
import helpFamilyIcon from "./assets/figma/help-family.png";
import helpCalendarIcon from "./assets/figma/help-calendar.svg";
import helpAddIcon from "./assets/figma/help-add.svg";
import houseShortcut from "./assets/figma/house-shortcut.png";
import listShortcut from "./assets/figma/lists-shortcut.png";
import footerCatBase from "./assets/figma/illustrations/footer-cat/base.svg";
import footerCatBaseEye from "./assets/figma/illustrations/footer-cat/base-eye.svg";
import footerCatBaseEyeShine from "./assets/figma/illustrations/footer-cat/base-eye-shine.svg";
import footerCatBaseStar from "./assets/figma/illustrations/footer-cat/base-star.svg";
import footerCatEar from "./assets/figma/illustrations/footer-cat/ear.svg";
import footerCatEarRight from "./assets/figma/illustrations/footer-cat/ear-right.svg";
import footerCatEmpty from "./assets/figma/illustrations/footer-cat/empty.svg";
import footerCatEmptyEyeLeft from "./assets/figma/illustrations/footer-cat/empty-eye-left.svg";
import footerCatEmptyEyeRight from "./assets/figma/illustrations/footer-cat/empty-eye-right.svg";
import footerCatEmptyEyeLeftShine from "./assets/figma/illustrations/footer-cat/empty-eye-left-shine.svg";
import footerCatEmptyEyeRightShine from "./assets/figma/illustrations/footer-cat/empty-eye-right-shine.svg";
import footerCatEmptyStar from "./assets/figma/illustrations/footer-cat/empty-star.svg";
import star from "./assets/figma/star.png";
import footerWave from "./assets/figma/home-foot-wave.svg";
import branchLeft from "./assets/figma/home-foot-branch-left.svg";
import branchCenter from "./assets/figma/home-foot-branch-center.svg";
import branchRight from "./assets/figma/home-foot-branch-right.svg";
import listsHero from "./assets/figma/illustrations/lists/b4915e7e-ecaa-44ed-908d-799b790b9413.svg";
import listsHeroExpanded from "./assets/figma/illustrations/lists/378e332e-1881-4729-9011-d674c9415741.svg";
import familyHomeHouse from "./assets/figma/illustrations/family-home/house.png";
import familyHomeShadow from "./assets/figma/illustrations/family-home/shadow.svg";
import familyHomeTail from "./assets/figma/illustrations/family-home/c705df6f-1f98-452f-b7d0-6a986745f8a9.svg";
import familyHomeLeg from "./assets/figma/illustrations/family-home/deb3ffd8-8118-482a-ac61-da320524c8c9.svg";
import familyHomeBody from "./assets/figma/illustrations/family-home/8dfa403e-41bf-44d7-bec1-e215f411ff97.svg";
import familyHomeFoot from "./assets/figma/illustrations/family-home/0e99f6da-afc2-4f7f-a134-987d8409aa02.svg";
import familyHomeClaw from "./assets/figma/illustrations/family-home/ad30dd76-58d3-463a-97cd-44171ff0e471.svg";
import familyHomeEyeShine from "./assets/figma/illustrations/family-home/3bcc181d-a99d-4d3d-9ae3-ba212da07506.svg";
import familyHomeHead from "./assets/figma/illustrations/family-home/fbb5a8ab-09d6-49ea-97b1-7e3384ca2e2b.svg";
import familyHomeEye from "./assets/figma/illustrations/family-home/7d0b87e5-d61c-4d54-aad9-087c066a8907.svg";
import familyHomeEyeMark from "./assets/figma/illustrations/family-home/3476f08f-7e06-41a2-bf51-e8598c528dbe.svg";
import familyHomeEyeMark2 from "./assets/figma/illustrations/family-home/330a75c2-7b79-4a73-ba7d-e40e5abf18bd.svg";
import familyHomeEar from "./assets/figma/illustrations/family-home/9956f1e4-049c-49d5-96a2-56828e7914e5.svg";
import familyHomeEar2 from "./assets/figma/illustrations/family-home/c1a773bf-161a-4acb-8757-e6e5c2fbd008.svg";
import familyHomePaw from "./assets/figma/illustrations/family-home/37755955-0f40-44c9-9a04-fe2ee73fe7c8.svg";
import familyHomePaw2 from "./assets/figma/illustrations/family-home/737f87a8-23fa-46f1-8490-1a2a82e0be6e.svg";
import familyHomeToe from "./assets/figma/illustrations/family-home/fee1a322-8c42-48f4-b2a1-510c4fa1ade7.svg";
import familyHomeToe2 from "./assets/figma/illustrations/family-home/620c4a50-aa9f-4de3-a03f-a1d04f923c5b.svg";
import familyHomeStar from "./assets/figma/illustrations/family-home/star-face.png";
import familyHomeStarLeft from "./assets/figma/illustrations/family-home/star-left.svg";
import familyHomeStarRight from "./assets/figma/illustrations/family-home/star-right.svg";
import familyHomeCatStar from "./assets/figma/illustrations/family-home/star-corner.svg";
import welcomeBody from "./assets/figma/illustrations/tea/welcome-body.svg";
import welcomeBranchRight from "./assets/figma/illustrations/tea/welcome-branch-right.svg";
import welcomeBranchLeft from "./assets/figma/illustrations/tea/welcome-branch-left.svg";
import welcomeHead from "./assets/figma/illustrations/tea/welcome-head.svg";
import welcomeDetail from "./assets/figma/illustrations/tea/welcome-detail.svg";
import welcomeCup from "./assets/figma/illustrations/tea/welcome-cup.svg";
import welcomeFloor from "./assets/figma/illustrations/tea/welcome-floor.svg";
import welcomeWave from "./assets/figma/illustrations/tea/welcome-wave.svg";
import helpBody from "./assets/figma/illustrations/tea/help-body.svg";
import helpBranchRight from "./assets/figma/illustrations/tea/help-branch-right.svg";
import helpBranchLeft from "./assets/figma/illustrations/tea/help-branch-left.svg";
import helpHead from "./assets/figma/illustrations/tea/help-head.svg";
import helpDetail from "./assets/figma/illustrations/tea/help-detail.svg";
import helpCup from "./assets/figma/illustrations/tea/help-cup.svg";
import helpFloor from "./assets/figma/illustrations/tea/help-floor.svg";
import helpWave from "./assets/figma/illustrations/tea/help-wave.svg";
import homeCatShadow from "./assets/figma/illustrations/training/home-cat/shadow.svg";
import homeCatBody from "./assets/figma/illustrations/training/home-cat/body.svg";
import homeCatHead from "./assets/figma/illustrations/training/home-cat/head.svg";
import homeCatEye from "./assets/figma/illustrations/training/home-cat/eye.svg";
import homeCatStar from "./assets/figma/illustrations/training/home-cat/star.png";
import homeCatEyeMark from "./assets/figma/illustrations/training/home-cat/eye-mark.svg";
import homeCatEyeMark2 from "./assets/figma/illustrations/training/home-cat/eye-mark-2.svg";
import homeCatEar from "./assets/figma/illustrations/training/home-cat/ear.svg";
import homeCatFoot from "./assets/figma/illustrations/training/home-cat/foot.svg";
import homeCatFoot2 from "./assets/figma/illustrations/training/home-cat/foot-2.svg";
import calendarCatBody from "./assets/figma/illustrations/training/calendar-cat/body.svg";
import calendarCatPaw from "./assets/figma/illustrations/training/calendar-cat/paw.svg";
import calendarCatFoot from "./assets/figma/illustrations/training/calendar-cat/foot.svg";
import calendarCatHead from "./assets/figma/illustrations/training/calendar-cat/head.svg";
import calendarCatEye from "./assets/figma/illustrations/training/calendar-cat/eye.svg";
import calendarCatShadow from "./assets/figma/illustrations/training/calendar-cat/shadow.svg";
import familyBlackShadow from "./assets/figma/illustrations/training/family-black-cat/shadow.svg";
import familyBlackBody from "./assets/figma/illustrations/training/family-black-cat/body.svg";
import familyBlackHead from "./assets/figma/illustrations/training/family-black-cat/head.svg";
import familyBlackEye from "./assets/figma/illustrations/training/family-black-cat/eye.svg";
import familyBlackStar from "./assets/figma/illustrations/training/family-black-cat/star.png";
import familyBlackMark1 from "./assets/figma/illustrations/training/family-black-cat/mark-1.svg";
import familyBlackMark2 from "./assets/figma/illustrations/training/family-black-cat/mark-2.svg";
import familyBlackMark3 from "./assets/figma/illustrations/training/family-black-cat/mark-3.svg";
import familyBlackEar from "./assets/figma/illustrations/training/family-black-cat/ear.svg";
import familyBlackDecor1 from "./assets/figma/illustrations/training/family-black-cat/decor-1.svg";
import familyBlackDecor2 from "./assets/figma/illustrations/training/family-black-cat/decor-2.svg";
import familyBlackDecor3 from "./assets/figma/illustrations/training/family-black-cat/decor-3.svg";
import familyBlackDecor4 from "./assets/figma/illustrations/training/family-black-cat/decor-4.svg";
import familyBlackDecorLine from "./assets/figma/illustrations/training/family-black-cat/decor-line.svg";
import familyBlackBadgeGeneral from "./assets/figma/illustrations/training/family-black-cat/badge-general.svg";
import familyBlackBadgeHealth from "./assets/figma/illustrations/training/family-black-cat/badge-health.svg";
import familyBlackBadgeHome from "./assets/figma/illustrations/training/family-black-cat/badge-home.svg";
import familyBlackLeg1 from "./assets/figma/illustrations/training/family-black-cat/decor-leg-1.svg";
import familyBlackLeg2 from "./assets/figma/illustrations/training/family-black-cat/decor-leg-2.svg";
import familyWhitePaw from "./assets/figma/illustrations/training/family-white-cat/paw.svg";
import familyWhiteTail from "./assets/figma/illustrations/training/family-white-cat/tail.svg";
import familyWhiteBody from "./assets/figma/illustrations/training/family-white-cat/body.svg";
import familyWhiteHead from "./assets/figma/illustrations/training/family-white-cat/head.svg";
import familyWhiteEye from "./assets/figma/illustrations/training/family-white-cat/eye.svg";
import familyWhiteEyeMark from "./assets/figma/illustrations/training/family-white-cat/eye-mark.svg";
import familyWhiteEar1 from "./assets/figma/illustrations/training/family-white-cat/ear-1.svg";
import familyWhiteEar2 from "./assets/figma/illustrations/training/family-white-cat/ear-2.svg";
import familyWhiteTailMark from "./assets/figma/illustrations/training/family-white-cat/tail-mark.svg";
import familyWhiteEyeDot from "./assets/figma/illustrations/training/family-white-cat/eye-dot.svg";
import familyWhiteEyeDot2 from "./assets/figma/illustrations/training/family-white-cat/eye-dot-2.svg";
import familyWhiteBow from "./assets/figma/illustrations/training/family-white-cat/bow.svg";
import familyWhiteStar from "./assets/figma/illustrations/training/family-white-cat/star.png";
import reminderCatTail from "./assets/figma/illustrations/training/notification-cat-tail.svg";
import reminderCatBody from "./assets/figma/illustrations/training/notification-cat-body.svg";
import reminderCatLeg from "./assets/figma/illustrations/training/notification-cat-leg.svg";
import reminderCatPaw from "./assets/figma/illustrations/training/notification-cat-paw.svg";
import reminderCatHead from "./assets/figma/illustrations/training/notification-cat-head.svg";
import reminderCatEye from "./assets/figma/illustrations/training/notification-cat-eye.svg";
import reminderCatEyeMark from "./assets/figma/illustrations/training/notification-cat-eye-mark.svg";
import reminderCatEyeMark2 from "./assets/figma/illustrations/training/notification-cat-eye-mark-2.svg";
import reminderCatEar from "./assets/figma/illustrations/training/notification-cat-ear.svg";
import reminderCatFoot from "./assets/figma/illustrations/training/notification-cat-foot.svg";
import reminderCatToe from "./assets/figma/illustrations/training/notification-cat-toe.svg";
import reminderCatToe2 from "./assets/figma/illustrations/training/notification-cat-toe-2.svg";
import reminderCatStar from "./assets/figma/illustrations/training/notification-cat-star.png";
import reminderHeadShadow from "./assets/figma/illustrations/training/head-cat-shadow.svg";
import reminderHead from "./assets/figma/illustrations/training/head-cat.svg";
import reminderHeadArrow from "./assets/figma/illustrations/training/head-cat-arrow.svg";
import reminderHeadArrowShort from "./assets/figma/illustrations/training/head-cat-arrow-short.svg";
import "./styles.css";

declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        initData?: string;
        ready?: () => void;
        expand?: () => void;
        close?: () => void;
        openTelegramLink?: (url: string) => void;
      };
    };
  }
}

type Screen = "loading" | "no-family" | "home" | "task" | "form" | "lists" | "family" | "help" | "onboarding";
type HomeMode = "nearest" | "calendar";

type Task = {
  id: number;
  text: string;
  deadline: string | null;
  deadlineTime: string | null;
  listId: string;
  listTitle: string | null;
  note: string | null;
  recurrence: string | null;
  snoozedUntil: string | null;
  reminderEnabled: boolean;
  completedAt: string | null;
};

type HomeSection = {
  id: string;
  title: string;
  date: string | null;
  tone: "green" | "purple";
  tasks: Task[];
};

type HomeData = {
  mode: HomeMode;
  today: string;
  selectedDate: string;
  stats: { today: number; overdue: number };
  calendar: { date: string; weekday: string; day: number; selected: boolean; hasTasks?: boolean }[];
  sections: HomeSection[];
};

type Category = { id: string; title: string; count: number; tasks: Task[] };
type ListsData = { categories: Category[]; missingPresets: { id: string; title: string }[] };
type FamilyData = {
  ownerChatId: number | null;
  canManageMembers: boolean;
  members: { chatId: number; name: string }[];
};
type MeData = { user: { chatId: number; name: string }; hasFamily: boolean };
type FormData = {
  text: string;
  deadline: string | null;
  deadlineTime: string | null;
  listId: string;
  note: string | null;
  reminderEnabled: boolean;
};

const categoryIcons: Record<string, string> = {
  general: homeGeneralIcon,
  health: healthIcon,
  home: homeIcon,
  shopping: shoppingIcon,
  work: workIcon,
  dacha: homeIcon,
  vacation: homeGeneralIcon,
};
const categoryColors: Record<string, string> = {
  general: "green",
  health: "purple",
  home: "orange",
  shopping: "pink",
  work: "blue",
  dacha: "orange",
  vacation: "purple",
};
const categoryNames: Record<string, string> = {
  general: "Общий",
  health: "Здоровье",
  home: "Дом",
  shopping: "Покупки",
  work: "Работа",
  dacha: "Дача",
  vacation: "Отпуск",
};

class ApiClient {
  private readonly initData = window.Telegram?.WebApp?.initData ?? "";

  async get<T>(path: string): Promise<T> {
    return this.request<T>(path, { method: "GET" });
  }

  async post<T>(path: string, body: unknown = {}): Promise<T> {
    return this.request<T>(path, { method: "POST", body: JSON.stringify(body) });
  }

  async patch<T>(path: string, body: unknown): Promise<T> {
    return this.request<T>(path, { method: "PATCH", body: JSON.stringify(body) });
  }

  async delete<T>(path: string): Promise<T> {
    return this.request<T>(path, { method: "DELETE" });
  }

  private async request<T>(path: string, init: RequestInit): Promise<T> {
    const headers = new Headers(init.headers);
    headers.set("Content-Type", "application/json");
    if (this.initData) headers.set("X-Telegram-Init-Data", this.initData);
    const response = await fetch(path, { ...init, headers, cache: "no-store" });
    const body = await response.json().catch(() => ({})) as { error?: string };
    if (!response.ok) {
      const message = response.status === 401
        ? "Откройте мини-приложение через бота"
        : response.status >= 500
          ? "Не удалось выполнить запрос"
          : body.error || `Ошибка запроса (${response.status})`;
      throw new ApiError(message, response.status);
    }
    return body as T;
  }
}

class ApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
  }
}

function App() {
  const api = useMemo(() => new ApiClient(), []);
  const [screen, setScreen] = useState<Screen>("loading");
  const [home, setHome] = useState<HomeData | null>(null);
  const [lists, setLists] = useState<ListsData | null>(null);
  const [family, setFamily] = useState<FamilyData | null>(null);
  const [me, setMe] = useState<MeData | null>(null);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [taskReturn, setTaskReturn] = useState<{ screen: "home" | "lists"; openListId: string } | null>(null);
  const [openListId, setOpenListId] = useState("");
  const [formEditing, setFormEditing] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [homeMode, setHomeMode] = useState<HomeMode>("nearest");
  const [selectedDate, setSelectedDate] = useState("");

  const refreshMe = useCallback(async () => {
    const data = await api.get<MeData>("/api/me");
    setMe(data);
    return data;
  }, [api]);

  const refreshHome = useCallback(async (mode = homeMode, date = selectedDate) => {
    const suffix = date ? `&date=${encodeURIComponent(date)}` : "";
    const data = await api.get<HomeData>(`/api/home?mode=${mode}${suffix}`);
    setHome(data);
    setHomeMode(mode);
    setSelectedDate(data.selectedDate);
    return data;
  }, [api, homeMode, selectedDate]);

  const refreshLists = useCallback(async () => {
    const data = await api.get<ListsData>("/api/lists");
    setLists(data);
    return data;
  }, [api]);

  const refreshFamily = useCallback(async () => {
    const data = await api.get<FamilyData>("/api/family");
    setFamily(data);
    return data;
  }, [api]);

  const reportError = useCallback((value: unknown) => {
    setError(value instanceof Error ? value.message : "Не удалось выполнить запрос");
    window.setTimeout(() => setError(""), 4200);
  }, []);

  const returnFromTask = useCallback(() => {
    const target = taskReturn?.screen ?? "home";
    setScreen(target);
    if (target === "home") {
      setOpenListId("");
      void refreshHome().catch(reportError);
    }
    setTaskReturn(null);
  }, [refreshHome, reportError, taskReturn]);

  useEffect(() => {
    window.Telegram?.WebApp?.ready?.();
    window.Telegram?.WebApp?.expand?.();
    void refreshMe().then((data) => {
      if (!data.hasFamily) {
        setScreen("no-family");
        return;
      }
      setScreen(localStorage.getItem("kotik-onboarding-seen") ? "home" : "onboarding");
    }).catch((reason: unknown) => {
      reportError(reason);
      setScreen("no-family");
    });
  }, [refreshMe, reportError]);

  useEffect(() => {
    if (screen !== "home" || !me?.hasFamily) return;
    void refreshHome().catch(reportError);
  }, [screen, me?.hasFamily, refreshHome, reportError]);

  useEffect(() => {
    if (screen === "lists") void refreshLists().catch(reportError);
    if (screen === "family") void refreshFamily().catch(reportError);
  }, [screen, refreshLists, refreshFamily, reportError]);

  const refreshVisible = useCallback(async () => {
    if (!me?.hasFamily) return;
    try {
      if (screen === "home") await refreshHome();
      if (screen === "lists") await refreshLists();
      if (screen === "family") await refreshFamily();
      if (screen === "task" || screen === "form") {
        const [latest] = await Promise.all([refreshLists(), refreshHome()]);
        const updated = latest.categories.flatMap((category) => category.tasks).find((task) => task.id === selectedTask?.id);
        if (updated) setSelectedTask(updated);
        else if (selectedTask) {
          setSelectedTask(null);
          returnFromTask();
        }
      }
    } catch (reason) {
      if (reason instanceof ApiError && reason.status === 403) {
        try {
          const current = await refreshMe();
          if (!current.hasFamily) {
            setHome(null);
            setLists(null);
            setFamily(null);
            setSelectedTask(null);
            setScreen("no-family");
            return;
          }
        } catch {
          // Keep the current page if the follow-up status check is temporarily unavailable.
        }
      }
      if (reason instanceof ApiError && reason.status === 404 && selectedTask) {
        setSelectedTask(null);
        returnFromTask();
        void refreshHome().catch(reportError);
        return;
      }
      reportError(reason);
    }
  }, [me?.hasFamily, screen, selectedTask?.id, refreshHome, refreshLists, refreshFamily, reportError, returnFromTask]);

  useEffect(() => {
    const onFocus = () => void refreshVisible();
    const onVisibility = () => {
      if (document.visibilityState === "visible") onFocus();
    };
    window.addEventListener("focus", onFocus);
    document.addEventListener("visibilitychange", onVisibility);
    const timer = window.setInterval(() => {
      if (document.visibilityState === "visible") onFocus();
    }, 5000);
    return () => {
      window.removeEventListener("focus", onFocus);
      document.removeEventListener("visibilitychange", onVisibility);
      window.clearInterval(timer);
    };
  }, [refreshVisible]);

  async function reloadHomeAndLists() {
    await Promise.all([refreshHome(), refreshLists()]);
  }

  async function completeTask(task: Task) {
    if (task.completedAt) return;
    setBusy(true);
    try {
      await api.post(`/api/tasks/${task.id}/complete`);
      await reloadHomeAndLists();
    } catch (reason) {
      reportError(reason);
    } finally {
      setBusy(false);
    }
  }

  async function saveTask(values: FormData) {
    setBusy(true);
    try {
      if (selectedTask && formEditing) await api.patch(`/api/tasks/${selectedTask.id}`, values);
      else await api.post("/api/tasks", values);
      await reloadHomeAndLists();
      setSelectedTask(null);
      setFormEditing(false);
      returnFromTask();
    } catch (reason) {
      reportError(reason);
    } finally {
      setBusy(false);
    }
  }

  async function deleteTask(task: Task) {
    setBusy(true);
    try {
      await api.delete(`/api/tasks/${task.id}`);
      await reloadHomeAndLists();
      setSelectedTask(null);
      setFormEditing(false);
      returnFromTask();
    } catch (reason) {
      reportError(reason);
    } finally {
      setBusy(false);
    }
  }

  function openTask(task: Task, source: "home" | "lists" = screen === "lists" ? "lists" : "home", openListId = "") {
    setSelectedTask(task);
    setTaskReturn({ screen: source, openListId });
    if (source === "lists") setOpenListId(openListId);
    setFormEditing(false);
    setScreen("task");
  }

  function openNewTask() {
    setSelectedTask(null);
    setFormEditing(true);
    setScreen("form");
  }

  function finishOnboarding() {
    localStorage.setItem("kotik-onboarding-seen", "1");
    setScreen("home");
  }

  const goHome = () => {
    setSelectedTask(null);
    setFormEditing(false);
    setTaskReturn(null);
    setOpenListId("");
    setScreen("home");
  };

  return (
    <main className={`app-shell screen-${screen}`}>
      {screen === "loading" && <div className="loading-state" aria-label="Загрузка" />}
      {screen === "no-family" && <NoFamilyScreen onBack={() => window.Telegram?.WebApp?.close?.()} />}
      {screen === "onboarding" && <Onboarding onDone={finishOnboarding} />}
      {screen === "home" && home && me && (
        <HomeScreen
          home={home}
          userName={me.user.name}
          loading={busy}
          onOpenAdd={openNewTask}
          onOpenFamily={() => setScreen("family")}
          onOpenLists={() => setScreen("lists")}
          onOpenHelp={() => setScreen("help")}
          onModeChange={(mode) => void refreshHome(mode, mode === "calendar" ? selectedDate : "").catch(reportError)}
          onDateChange={(date) => void refreshHome("calendar", date).catch(reportError)}
          onComplete={completeTask}
          onOpenTask={openTask}
        />
      )}
      {(screen === "task" || screen === "form") && (
        <TaskFormScreen
          key={`${screen}-${selectedTask?.id ?? "new"}-${formEditing}`}
          task={selectedTask}
          returnToLists={taskReturn?.screen === "lists"}
          editing={screen === "form" && formEditing}
          categories={lists?.categories ?? []}
          busy={busy}
          onBack={() => screen === "task" ? returnFromTask() : selectedTask ? setScreen("task") : returnFromTask()}
          onEdit={() => { setFormEditing(true); setScreen("form"); }}
          onSave={saveTask}
          onDelete={deleteTask}
          onLoadLists={refreshLists}
          reportError={reportError}
        />
      )}
      {screen === "lists" && lists && (
        <ListsScreen
          data={lists}
          openId={openListId}
          onOpenIdChange={setOpenListId}
          onBack={goHome}
          onComplete={completeTask}
          onOpenTask={(task, openListId) => openTask(task, "lists", openListId)}
          onEnablePreset={async (id) => {
            try {
              await api.post("/api/lists", { presetId: id });
              await refreshLists();
            } catch (reason) {
              reportError(reason);
            }
          }}
        />
      )}
      {screen === "family" && family && (
        <FamilyScreen
          data={family}
          api={api}
          onBack={goHome}
          onReload={refreshFamily}
          reportError={reportError}
        />
      )}
      {screen === "help" && <HelpScreen onBack={goHome} />}
      {error && <div className="toast" role="status">{error}</div>}
    </main>
  );
}

function HomeScreen({
  home,
  userName,
  loading,
  onOpenAdd,
  onOpenFamily,
  onOpenLists,
  onOpenHelp,
  onModeChange,
  onDateChange,
  onComplete,
  onOpenTask,
}: {
  home: HomeData;
  userName: string;
  loading: boolean;
  onOpenAdd: () => void;
  onOpenFamily: () => void;
  onOpenLists: () => void;
  onOpenHelp: () => void;
  onModeChange: (mode: HomeMode) => void;
  onDateChange: (date: string) => void;
  onComplete: (task: Task) => void;
  onOpenTask: (task: Task) => void;
}) {
  const calendarStripRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (home.mode !== "calendar") return;
    calendarStripRef.current
      ?.querySelector<HTMLButtonElement>("button.selected")
      ?.scrollIntoView({ block: "nearest", inline: "nearest" });
  }, [home.mode, home.selectedDate, home.calendar]);

  return (
    <>
      <section className="home-shortcuts">
        <Shortcut image={houseShortcut} label="Семья" onClick={onOpenFamily} />
        <Shortcut image={listShortcut} label="Списки" onClick={onOpenLists} />
      </section>
      <section className="greeting">
        <h1>{greeting()},<br />как ваши <span>ДЕЛА?</span></h1>
        <img src={star} alt="" />
      </section>
      <section className="stats-row" aria-label="Сводка дел">
        <StatPill tone="green" label="Сегодня дел" value={home.stats.today} icon="clock" />
        <StatPill tone="purple" label="Просрочено" value={home.stats.overdue} icon="sad" />
      </section>
      <section className={`mode-tabs${home.mode === "calendar" ? " calendar-tabs" : ""}`} aria-label="Режим списка дел">
        <button className={home.mode === "nearest" ? "selected" : ""} onClick={() => onModeChange("nearest")}>Ближайшие задачи</button>
        <button className={home.mode === "calendar" ? "selected" : ""} onClick={() => onModeChange("calendar")}>Что дальше?</button>
      </section>
      {home.mode === "calendar" && (
        <section ref={calendarStripRef} className="calendar-strip" aria-label="Календарь">
          {home.calendar.map((day) => (
            <button
              key={day.date}
              className={day.selected ? "selected" : ""}
              onClick={() => onDateChange(day.date)}
              aria-label={`${day.weekday} ${day.day}`}
            >
              <span>{day.weekday}</span><strong>{day.day}</strong><i className={day.hasTasks ? "has-tasks" : ""} />
            </button>
          ))}
        </section>
      )}
      <section className={`home-sections ${loading ? "is-loading" : ""}`}>
        {home.sections.map((section, index) => (
          <DateSection
            key={section.id}
            section={section}
            previousHasTasks={index > 0 && home.sections[index - 1].tasks.length > 0}
            today={home.today}
            onComplete={onComplete}
            onOpenTask={onOpenTask}
          />
        ))}
      </section>
      <BottomCatBar onAdd={onOpenAdd} onHelp={onOpenHelp} empty={home.sections.every((section) => section.tasks.length === 0)} />
    </>
  );
}

function Shortcut({ image, label, onClick }: { image: string; label: string; onClick: () => void }) {
  return (
    <button className="shortcut" onClick={onClick}>
      <img src={image} alt="" /><span>{label}</span><img className="shortcut-arrow" src={shortcutArrow} alt="" />
    </button>
  );
}

function StatPill({ tone, label, value, icon }: { tone: string; label: string; value: number; icon: string }) {
  return (
    <div className={`stat-pill tone-${tone}`}>
      <img className={`stat-icon stat-icon-${icon}`} src={icon === "clock" ? statClockIcon : value === 0 ? statNoOverdueIcon : statOverdueIcon} alt="" />
      <span className="stat-copy"><small>{label}</small><strong>{value}</strong></span>
    </div>
  );
}

function DateSection({
  section,
  previousHasTasks,
  today,
  onComplete,
  onOpenTask,
}: {
  section: HomeSection;
  previousHasTasks: boolean;
  today: string;
  onComplete: (task: Task) => void;
  onOpenTask: (task: Task) => void;
}) {
  return (
    <section className={`date-section section-${section.tone}`} data-previous-has-tasks={previousHasTasks ? "true" : "false"}>
      <h2><i />{section.title}{section.date && <small>({formatRuDate(section.date)})</small>}</h2>
      <div className="task-stack">
        {section.tasks.map((task) => (
          <TaskCard key={task.id} task={task} today={today} onComplete={onComplete} onOpen={onOpenTask} />
        ))}
      </div>
    </section>
  );
}

function TaskCard({
  task,
  today,
  onComplete,
  onOpen,
}: {
  task: Task;
  today: string;
  onComplete: (task: Task) => void;
  onOpen: (task: Task) => void;
}) {
  const isOverdue = !!task.deadline && task.deadline < today && !task.completedAt;
  return (
    <article className={`task-card ${task.completedAt ? "completed" : ""} ${isOverdue ? "overdue" : ""}`}>
      <button
        className={`task-check ${task.completedAt ? "checked" : isOverdue ? "overdue" : ""}`}
        onClick={() => onComplete(task)}
        disabled={!!task.completedAt}
        aria-label={task.completedAt ? "Выполнено" : "Отметить выполненным"}
      ><img src={task.completedAt ? taskCheckDoneIcon : isOverdue ? taskCheckOverdueIcon : taskCheckEmptyIcon} alt="" /></button>
      <button className="task-card-body" onClick={() => onOpen(task)}>
        <span className="task-copy"><strong>{task.text}</strong><small className={`category-chip tone-${categoryColors[task.listId] || "green"}`}>{task.listTitle || categoryNames[task.listId] || "Общий"}</small></span>
        <span className="task-time">
          {task.deadline && !task.deadlineTime
            ? <small className="all-day-label">Весь день</small>
            : <><small>{relativeDateLabel(task.deadline, today)}</small><b>{task.deadlineTime?.replace(/^0(?=\d:)/, "") || ""}</b></>}
        </span>
        <img className={`task-category-icon tone-${categoryColors[task.listId] || "green"}`} src={categoryIcons[task.listId] || homeGeneralIcon} alt="" />
      </button>
    </article>
  );
}

function BottomCatBar({ onAdd, onHelp, empty }: { onAdd: () => void; onHelp: () => void; empty: boolean }) {
  return (
    <footer className="bottom-cat-bar">
      <img className="footer-wave" src={footerWave} alt="" />
      <img className="footer-branch left" src={branchLeft} alt="" />
      <img className="footer-branch center" src={branchCenter} alt="" />
      <img className="footer-branch right" src={branchRight} alt="" />
      <img className="footer-branch far-right" src={footerBranchFarRight} alt="" />
      <button className="footer-cat-button" onClick={onAdd} aria-label="Добавить дело">
        <FooterCatArt empty={empty} /><span className="footer-cat-label">Нажми на котика -<br />добавь задачу</span>
      </button>
      <button className="footer-help" onClick={onHelp}><img src={helpIcon} alt="" />Нужна помощь?</button>
    </footer>
  );
}

function FooterCatArt({ empty }: { empty: boolean }) {
  if (empty) {
    return <span className="footer-cat-art footer-cat-empty" aria-hidden="true" data-node-id="16:246">
      <img className="footer-cat-shape" src={footerCatEmpty} />
      <span className="footer-cat-empty-star"><span><img src={footerCatEmptyStar} /></span></span>
      <img className="footer-cat-empty-eye left" src={footerCatEmptyEyeLeft} />
      <img className="footer-cat-empty-eye right" src={footerCatEmptyEyeRight} />
      <img className="footer-cat-ear left" src={footerCatEar} />
      <img className="footer-cat-ear right" src={footerCatEarRight} />
      <span className="footer-cat-empty-eye-shine left"><img src={footerCatEmptyEyeLeftShine} /></span>
      <span className="footer-cat-empty-eye-shine right"><img src={footerCatEmptyEyeRightShine} /></span>
    </span>;
  }
  return <span className="footer-cat-art footer-cat-base" aria-hidden="true" data-node-id="16:153">
    <img className="footer-cat-shape" src={footerCatBase} />
    <span className="footer-cat-base-eye-shine"><span><img src={footerCatBaseEyeShine} /></span></span>
    <img className="footer-cat-base-eye left" src={footerCatBaseEye} />
    <img className="footer-cat-base-eye right" src={footerCatBaseEye} />
    <img className="footer-cat-ear left" src={footerCatEar} />
    <img className="footer-cat-ear right" src={footerCatEarRight} />
    <span className="footer-cat-base-star"><span><img src={footerCatBaseStar} /></span></span>
  </span>;
}

function normalizeTaskTime(value: string): string | null {
  const trimmed = value.trim();
  if (!trimmed) return "";

  let hoursText: string;
  let minutesText: string;
  if (/^\d{1,2}:\d{1,2}$/.test(trimmed)) {
    [hoursText, minutesText] = trimmed.split(":");
  } else if (/^\d{4}$/.test(trimmed)) {
    hoursText = trimmed.slice(0, 2);
    minutesText = trimmed.slice(2);
  } else if (/^\d{3}$/.test(trimmed)) {
    hoursText = trimmed.slice(0, 1);
    minutesText = trimmed.slice(1);
  } else {
    return null;
  }

  const hours = Number(hoursText);
  const minutes = Number(minutesText);
  if (hours > 23 || minutes > 59) return null;
  return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}`;
}

function TaskFormScreen({
  task,
  returnToLists,
  editing,
  categories,
  busy,
  onBack,
  onEdit,
  onSave,
  onDelete,
  onLoadLists,
  reportError,
}: {
  task: Task | null;
  returnToLists: boolean;
  editing: boolean;
  categories: Category[];
  busy: boolean;
  onBack: () => void;
  onEdit: () => void;
  onSave: (values: FormData) => Promise<void>;
  onDelete: (task: Task) => Promise<void>;
  onLoadLists: () => Promise<ListsData>;
  reportError: (reason: unknown) => void;
}) {
  const [text, setText] = useState(task?.text ?? "");
  const [deadline, setDeadline] = useState<string | null>(task?.deadline ?? null);
  const [deadlineTime, setDeadlineTime] = useState(task?.deadlineTime ?? "");
  const [listId, setListId] = useState(task?.listId ?? "general");
  const [note, setNote] = useState(task?.note ?? "");
  const [reminderEnabled, setReminderEnabled] = useState(task?.reminderEnabled ?? false);
  const [categoryOpen, setCategoryOpen] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(false);
  const [deadlineTimeError, setDeadlineTimeError] = useState("");
  const [datePickerFallback, setDatePickerFallback] = useState(false);
  const datePickerRef = useRef<HTMLInputElement>(null);
  const [loadedCategories, setLoadedCategories] = useState(categories);
  const [saving, setSaving] = useState(false);
  const readOnly = !!task && !editing;
  const today = useIsoToday();
  const tomorrow = addIsoDays(today, 1);
  const selected = loadedCategories.find((category) => category.id === listId);

  function openDatePicker() {
    const input = datePickerRef.current;
    if (!input) return;
    try {
      if (typeof input.showPicker === "function") {
        setDatePickerFallback(false);
        input.showPicker();
        return;
      }
    } catch {
      // If the browser rejects the native picker, show a usable input instead.
    }
    setDatePickerFallback(true);
    window.requestAnimationFrame(() => input.focus());
  }

  useEffect(() => {
    if (loadedCategories.length === 0) void onLoadLists().then((data) => setLoadedCategories(data.categories)).catch(reportError);
  }, [loadedCategories.length, onLoadLists, reportError]);

  useEffect(() => {
    if (editing || !task) return;
    setText(task.text);
    setDeadline(task.deadline);
    setDeadlineTime(task.deadlineTime ?? "");
    setListId(task.listId);
    setNote(task.note ?? "");
    setReminderEnabled(task.reminderEnabled);
    setDeleteConfirm(false);
  }, [editing, task]);

  async function submit() {
    const normalizedTime = normalizeTaskTime(deadlineTime);
    if (normalizedTime === null) {
      setDeadlineTimeError("Введите время от 00:00 до 23:59.");
      document.getElementById("task-time")?.focus();
      return;
    }
    if (normalizedTime && !deadline) {
      setDeadlineTimeError("Выберите дату для напоминания о времени.");
      return;
    }
    setDeadlineTime(normalizedTime);
    setDeadlineTimeError("");
    setSaving(true);
    try {
      await onSave({
        text: text.trim(),
        deadline,
        deadlineTime: deadline && normalizedTime ? normalizedTime : null,
        listId,
        note: note.trim() || null,
        reminderEnabled: !!deadline && !!normalizedTime && reminderEnabled,
      });
    } finally {
      setSaving(false);
    }
  }

  const canSave = text.trim().length > 0 && (!deadlineTime || !!deadline) && !busy && !saving;
  return (
    <section className="task-form-screen">
      <ScreenHeader title="Добавить дело" onBack={onBack} />
      <label className="form-label" htmlFor="task-text">Что нужно сделать?</label>
      <div className={`form-control task-name-control ${readOnly ? "read-only" : ""}`}>
        {readOnly ? <span>{text}</span> : <input id="task-text" value={text} onChange={(event) => setText(event.target.value)} placeholder="Введите задачу..." autoComplete="off" />}
        {readOnly ? <button className="field-action" aria-label="Редактировать" onClick={onEdit}><img src={pencilIcon} alt="" /></button> : <img className="field-icon" src={pencilIcon} alt="" />}
      </div>

      <label className="form-label">Дата</label>
      <div className="deadline-grid">
        <DateChoice active={!deadline} disabled={readOnly} label="Без дедлайна" onClick={() => { setDeadline(null); setDeadlineTime(""); setDeadlineTimeError(""); setReminderEnabled(false); }} />
        <DateChoice active={deadline === today} disabled={readOnly} label="Сегодня" onClick={() => setDeadline(today)} />
        <DateChoice active={deadline === tomorrow} disabled={readOnly} label="Завтра" onClick={() => setDeadline(tomorrow)} />
        <button
          className={`date-choice ${deadline && deadline !== today && deadline !== tomorrow ? "active" : ""}`}
          disabled={readOnly}
          onClick={openDatePicker}
        ><span className="calendar-icon" aria-hidden="true" />Другая дата</button>
      </div>
      <input
        ref={datePickerRef}
        className={`native-date-picker${datePickerFallback ? " fallback" : ""}`}
        type="date"
        aria-label="Выберите дату"
        tabIndex={datePickerFallback ? 0 : -1}
        value={deadline ?? today}
        min={today}
        onChange={(event) => { setDeadline(event.target.value || null); setDatePickerFallback(false); }}
      />

      <label className="form-label muted-label" htmlFor="task-time">Время <span>(необязательно)</span></label>
      {readOnly ? (
        <div className="form-control time-control read-only">
          <img src={timeIcon} alt="" />
          <span className={`time-value ${deadlineTime ? "selected" : "placeholder"}`}>{deadlineTime || "Добавить время"}</span>
        </div>
      ) : (
        <label className="form-control time-control" htmlFor="task-time">
          <img src={timeIcon} alt="" />
          <input
            id="task-time"
            type="text"
            inputMode="numeric"
            autoComplete="off"
            maxLength={5}
            aria-label="Время"
            aria-invalid={deadlineTimeError ? "true" : undefined}
            aria-describedby={deadlineTimeError ? "task-time-error" : undefined}
            placeholder="Добавить время"
            value={deadlineTime}
            onChange={(event) => {
              if (!deadline) setDeadline(today);
              setDeadlineTime(event.currentTarget.value.replace(/[^\d:]/g, "").slice(0, 5));
              if (deadlineTimeError) setDeadlineTimeError("");
            }}
            onBlur={(event) => {
              const normalized = normalizeTaskTime(event.currentTarget.value);
              if (normalized === null) setDeadlineTimeError("Введите время от 00:00 до 23:59.");
              else {
                setDeadlineTime(normalized);
                setDeadlineTimeError("");
              }
            }}
          />
        </label>
      )}
      {deadlineTimeError && <small className="time-input-error" id="task-time-error" role="alert">{deadlineTimeError}</small>}
      {!!deadlineTime && !task && <ReminderToggle enabled={reminderEnabled} disabled={readOnly} onChange={setReminderEnabled} />}

      {(!text.trim() || categoryOpen) && <label className="form-label" id="category-label">Что нужно сделать?</label>}
      <div className={`category-select ${categoryOpen ? "open" : ""} ${readOnly ? "read-only" : ""} ${!text.trim() || categoryOpen ? "has-label" : "no-label"}`}>
        <button className="category-current" disabled={readOnly} aria-expanded={categoryOpen} onClick={() => setCategoryOpen(!categoryOpen)}>
          <CategoryIcon id={listId} /><span>{selected?.id === "general" ? "Общий" : selected?.title || categoryNames[listId] || "Общий"}</span>
          <img className={categoryOpen ? "up" : ""} src={dropdownIcon} alt="" />
        </button>
        {categoryOpen && sortFormCategories(loadedCategories).filter((category) => category.id !== listId).map((category) => (
          <button
            className="category-option"
            key={category.id}
            onClick={() => { setListId(category.id); setCategoryOpen(false); }}
          ><CategoryIcon id={category.id} /><span>{category.title}</span></button>
        ))}
      </div>

      <label className="form-label muted-label" htmlFor="task-note">Заметка <span>(необязательно)</span></label>
      {readOnly
        ? <div className="note-readonly">{note || <span className="placeholder">Добавить заметку...</span>}</div>
        : <textarea id="task-note" className="note-field" value={note} placeholder="Добавить заметку..." rows={1} onChange={(event) => { setNote(event.target.value); event.currentTarget.style.height = "auto"; event.currentTarget.style.height = `${event.currentTarget.scrollHeight}px`; }} />}

      {readOnly ? (
        <button className="primary-button" onClick={onEdit}><img src={star} alt="" />Редактировать</button>
      ) : (
        <>
          <button className="primary-button" disabled={!canSave} onClick={() => void submit()}><img src={star} alt="" />{task ? "Сохранить изменения" : "Добавить задачу"}</button>
          {task && <button className={`delete-task-button ${deleteConfirm ? "confirming" : ""}`} onClick={() => setDeleteConfirm(true)}>Удалить дело</button>}
        </>
      )}
      {deleteConfirm && task && (
        <ConfirmDialog title="Вы уверенны?" onConfirm={() => void onDelete(task)} onCancel={() => setDeleteConfirm(false)} />
      )}
    </section>
  );
}

function ScreenHeader({ title, onBack }: { title: string; onBack: () => void }) {
  return (
    <header className="screen-header">
      <button className="back-button" onClick={onBack} aria-label="Назад"><img src={backIcon} alt="" /></button>
      <h1>{title}</h1>
    </header>
  );
}

function DateChoice({ active, disabled, label, onClick }: { active: boolean; disabled: boolean; label: string; onClick: () => void }) {
  return <button className={`date-choice ${active ? "active" : ""}`} disabled={disabled} onClick={onClick}><i />{label}</button>;
}

function ReminderToggle({ enabled, disabled = false, onChange }: { enabled: boolean; disabled?: boolean; onChange: (enabled: boolean) => void }) {
  return (
    <div className="reminder-control">
      <div className="reminder-row"><span><img src={bellIcon} alt="" />Напомнить</span><button className={`toggle ${enabled ? "on" : ""}`} disabled={disabled} aria-label="Напомнить" aria-pressed={enabled} onClick={() => onChange(!enabled)}><i /></button></div>
      <small>{enabled ? "Напоминание придёт в день события" : "Уведомление не будет отправлено"}</small>
    </div>
  );
}

function CategoryIcon({ id }: { id: string }) {
  return <img className={`category-icon tone-${categoryColors[id] || "green"}`} src={categoryIcons[id] || homeGeneralIcon} alt="" />;
}

function ListsScreen({
  data,
  openId,
  onOpenIdChange,
  onBack,
  onComplete,
  onOpenTask,
  onEnablePreset,
}: {
  data: ListsData;
  openId: string;
  onOpenIdChange: (id: string) => void;
  onBack: () => void;
  onComplete: (task: Task) => void;
  onOpenTask: (task: Task, openListId: string) => void;
  onEnablePreset: (id: string) => Promise<void>;
}) {
  const [presetsOpen, setPresetsOpen] = useState(false);
  const today = useIsoToday();
  return (
    <section className="lists-screen">
      <ScreenHeader title="Списки" onBack={onBack} />
      <img className="lists-hero" src={openId ? listsHeroExpanded : listsHero} alt="" />
      <p className="screen-intro">Все дела распределяются по категориям,<br />чтобы ничего не потерялось</p>
      <div className="accordion-list">
        {sortCategories(data.categories).map((category) => (
          <article className={`category-accordion ${openId === category.id ? "expanded" : ""}`} key={category.id}>
            <button className="accordion-heading" onClick={() => onOpenIdChange(openId === category.id ? "" : category.id)} aria-expanded={openId === category.id}>
              <span className={`category-icon-bubble tone-${categoryColors[category.id] || "green"}`}><CategoryIcon id={category.id} /></span>
              <strong>{category.id === "general" ? "Общее" : category.title}</strong><b className="category-count">{category.count}</b><img className={openId === category.id ? "up" : ""} src={dropdownIcon} alt="" />
            </button>
            {openId === category.id && (
              <div className="accordion-tasks">
                {category.tasks.length ? category.tasks.map((task) => (
                  <TaskCard key={task.id} task={task} today={today} onComplete={onComplete} onOpen={(item) => onOpenTask(item, category.id)} />
                )) : <p className="empty-category">Пока нет дел</p>}
              </div>
            )}
          </article>
        ))}
      </div>
      <section className="preset-area">
        <button className="preset-toggle" onClick={() => setPresetsOpen(!presetsOpen)}>
          <img src={listAddIcon} alt="" />Добавить категорию
        </button>
        <p>Пока доступны только базовые<br />категории</p>
        {presetsOpen && <div className="preset-options">
          {data.missingPresets.length ? data.missingPresets.map((preset) => (
            <button key={preset.id} onClick={() => void onEnablePreset(preset.id).then(() => setPresetsOpen(false))}><CategoryIcon id={preset.id} />{preset.title}</button>
          )) : <small>Все базовые категории добавлены</small>}
        </div>}
      </section>
    </section>
  );
}

function FamilyScreen({
  data,
  api,
  onBack,
  onReload,
  reportError,
}: {
  data: FamilyData;
  api: ApiClient;
  onBack: () => void;
  onReload: () => Promise<FamilyData>;
  reportError: (reason: unknown) => void;
}) {
  const [confirmChatId, setConfirmChatId] = useState<number | null>(null);
  const [invitation, setInvitation] = useState("");
  const [copyNotice, setCopyNotice] = useState("");
  const member = data.members.find((item) => item.chatId === confirmChatId);

  async function invite() {
    try {
      const response = await api.post<{ code: string; botLink: string | null }>("/api/family/invite");
      const link = response.botLink;
      setInvitation(link || `Код приглашения: ${response.code}`);
      setCopyNotice("");
      if (link) {
        try {
          if (!navigator.clipboard?.writeText) return;
          await navigator.clipboard.writeText(link);
          setCopyNotice("Ссылка скопирована");
          window.setTimeout(() => setCopyNotice(""), 2400);
        } catch {
          // Keep the invite link visible if clipboard access is denied.
        }
      }
    } catch (reason) {
      reportError(reason);
    }
  }

  return (
    <section className="family-screen">
      <ScreenHeader title="Семья" onBack={onBack} />
      <FamilyHeroArt />
      <p className="screen-intro">Здесь те, кто вместе<br />планирует и делает важное</p>
      <div className="member-list">
        {data.members.map((item, index) => (
          <article className="member-row" key={item.chatId}>
            <span className={`member-avatar avatar-${index % 4}`}>{initial(item.name)}</span>
            <strong>{item.name}</strong>
            {item.chatId === data.ownerChatId && <span className="owner-badge"><img src={creatorStarIcon} alt="" />Создатель</span>}
            {data.canManageMembers && <button className="member-remove" disabled={item.chatId === data.ownerChatId} onClick={() => item.chatId !== data.ownerChatId && setConfirmChatId(item.chatId)} aria-label={item.chatId === data.ownerChatId ? "Нельзя удалить создателя" : `Удалить ${item.name}`}><img src={memberTrashIcon} alt="" /></button>}
          </article>
        ))}
      </div>
      <button className="invite-box" onClick={() => void invite()}>
        <strong><img className="invite-link-icon" src={inviteLinkIcon} alt="" />{invitation ? "Ссылка для приглашения" : "Пригласить в семью"}</strong>
        <small>{copyNotice || invitation || "Отправьте ссылку и пригласите\nновых участников"}</small>
      </button>
      {confirmChatId && member && (
        <ConfirmDialog
          title="Вы уверены?"
          onCancel={() => setConfirmChatId(null)}
          onConfirm={async () => {
            try {
              await api.delete(`/api/family/members/${confirmChatId}`);
              setConfirmChatId(null);
              await onReload();
            } catch (reason) {
              reportError(reason);
            }
          }}
        />
      )}
    </section>
  );
}

function FamilyHeroArt() {
  return <div className="family-hero-art" aria-hidden="true">
    <img className="family-hero-ground" src={familyHomeShadow} />
    <img className="family-hero-house" src={familyHomeHouse} />
    <img className="family-hero-star-left" src={familyHomeStarLeft} />
    <img className="family-hero-star-right" src={familyHomeStarRight} />
    <div className="family-hero-cat">
      <img className="family-hero-tail" src={familyHomeTail} />
      <img className="family-hero-leg" src={familyHomeLeg} />
      <img className="family-hero-body" src={familyHomeBody} />
      <img className="family-hero-foot" src={familyHomeFoot} />
      <img className="family-hero-claw" src={familyHomeClaw} />
      <span className="family-hero-head">
        <span className="family-hero-head-core">
          <img className="family-hero-head-shape" src={familyHomeHead} />
          <img className="family-hero-eye-shine" src={familyHomeEyeShine} />
          <img className="family-hero-eye-left" src={familyHomeEye} />
          <span className="family-hero-star"><span><img src={familyHomeStar} /></span></span>
          <img className="family-hero-eye-mark-left" src={familyHomeEyeMark} />
          <img className="family-hero-eye-mark-right" src={familyHomeEyeMark2} />
          <img className="family-hero-ear-left" src={familyHomeEar} />
          <img className="family-hero-ear-right" src={familyHomeEar2} />
        </span>
      </span>
      <img className="family-hero-paw" src={familyHomePaw} />
      <img className="family-hero-paw-left" src={familyHomePaw2} />
      <img className="family-hero-toe" src={familyHomeToe} />
      <img className="family-hero-toe-right" src={familyHomeToe2} />
      <img className="family-hero-cat-star" src={familyHomeCatStar} />
    </div>
  </div>;
}

function ConfirmDialog({ title, onConfirm, onCancel }: { title: string; onConfirm: () => void | Promise<void>; onCancel: () => void }) {
  return (
    <div className="dialog-backdrop" role="presentation">
      <section className="confirm-dialog" role="dialog" aria-modal="true" aria-label={title}>
        <h2>{title}</h2>
        <div><button onClick={onConfirm}>Да</button><button className="confirm-primary" onClick={onCancel}>Нет</button></div>
        <img className="dialog-sprig" src={dialogSprigIcon} alt="" />
      </section>
    </div>
  );
}

function HelpScreen({ onBack }: { onBack: () => void }) {
  return (
    <section className="help-screen">
      <h2 className="help-title">Добро пожаловать! <img src={star} alt="" /></h2>
      <p className="help-subtitle">Организуйте дела<br />без лишнего стресса</p>
      <TeaIllustration variant="help" className="help-hero" />
      <div className="help-items">
        <HelpItem title="Главная" text="Тут отображаются дела на сегодня, завтра и то, что вы пропустили" image={helpListIcon} />
        <HelpItem title="Что дальше?" text="Используйте календарь, чтобы увидеть дела на будущие дни" image={helpCalendarIcon} />
        <HelpItem title="Семья и списки" text="Добавляйте членов семьи, просматривайте или создавайте новые списки дел" image={helpFamilyIcon} />
        <HelpItem title="Добавить дело" text="Нажмите на котика, чтобы быстро добавить новое дело" image={helpAddIcon} />
      </div>
      <button className="primary-button help-return" onClick={onBack}><img src={star} alt="" />Вернуться к делам</button>
    </section>
  );
}

function HelpItem({ title, text, image }: { title: string; text: string; image: string }) {
  return <article className="help-item"><span><img src={image} alt="" /></span><div><strong>{title}</strong><small>{text}</small></div></article>;
}

function Onboarding({ onDone }: { onDone: () => void }) {
  const [step, setStep] = useState(0);
  if (step === 0) {
    return (
      <section className="welcome-screen">
        <article className="welcome-card">
          <h1>Добро пожаловать! <img src={star} alt="" /></h1>
          <p>Организуйте дела<br />без лишнего стресса</p>
          <TeaIllustration variant="welcome" className="welcome-illustration" />
          <footer><button onClick={onDone}>Пропустить</button><button className="small-primary" onClick={() => setStep(1)}>Обучение</button></footer>
        </article>
      </section>
    );
  }
  const slides = [
    { title: "Главное — под рукой", text: "На главной отображаются просроченные, сегодняшие и завтрашние дела.", artwork: <OnboardingHome /> },
    { title: "Планируйте заранее", text: <>В разделе «Что дальше?»<br />вы видите дела на следующие дни</>, artwork: <OnboardingCalendar /> },
    { title: "Организуйте дела вместе", text: <>Создавайте новые категории<br />и приглашайте семью</>, artwork: <OnboardingFamily /> },
    { title: "Вноси дела мгновенно!", text: <>Нажмите на котика, чтобы добавить дело.<br />Включите уведомление и мы напомнили<br />о нём</>, artwork: <OnboardingReminder /> },
  ];
  const slide = slides[step - 1];
  return (
    <section className="onboarding-screen">
      <article className={`onboarding-card onboarding-step-${step}`}>
        <strong className="step-count">{step}/4</strong>
        <div className="onboarding-artwork">{slide.artwork}</div>
        <h1>{slide.title}</h1>
        <p>{slide.text}</p>
        <div className="step-dots">{slides.map((_, index) => <i key={index} className={index === step - 1 ? "active" : ""} />)}</div>
        <footer><button onClick={onDone}>Пропустить</button><button className="small-primary" onClick={() => step === 4 ? onDone() : setStep(step + 1)}>{step === 4 ? <><img src={star} alt="" />Начать</> : <>Дальше <img className="next-arrow" src={[onboardingArrow1, onboardingArrow2, onboardingArrow3][step - 1]} alt="" /></>}</button></footer>
      </article>
    </section>
  );
}

function OnboardingHome() {
  return <div className="mini-home-art">
    <div className="mini-home-line">Просрочено</div>
    <MiniTask checked="overdue" title="Купить корм" category="Покупки" timeLabel="Вчера" time="18:30" mutedTime />
    <div className="mini-home-line green-line">Сегодня <small>(10.05.2026)</small></div>
    <MiniTask checked="done" title="Позвонить маме" category="Общий" timeLabel="Сегодня" time="14:30" />
    <div className="mini-home-line green-line">Завтра <small>(11.05.2026)</small></div>
    <MiniTask checked="empty" title="Полить цветы" category="Дом" timeLabel="Сегодня" time="18:30" />
    <HomeTrainingCat />
  </div>;
}

function OnboardingCalendar() {
  const days = ["Вт", "Ср", "Чт", "Пт", "Сб", "Вс", "Пн", "Вт", "Ср", "Чт"];
  return <div className="mini-calendar-art">
    <div className="mini-week">{days.map((day, index) => <span className={index === 3 ? "selected" : ""} key={`${day}-${index}`}>{day}<b>{10 + index}</b>{[0, 3, 4, 5, 6].includes(index) && <i />}</span>)}</div>
    <div className="mini-home-line">Просрочено</div>
    <strong className="mini-selected-date"><i />13.05.2026</strong>
    <MiniTask checked="empty" title="Приборка" category="Дом" timeLabel="Сегодня" time="14:30" />
    <MiniTask checked="empty" title="Тренировка" category="Здоровье" timeLabel="Сегодня" time="18:30" />
    <div className="mini-home-line green-line mini-tomorrow-line">Завтра <small>(14.05.2026)</small></div>
    <CalendarTrainingCat />
  </div>;
}

function MiniTask({ checked, title, category, timeLabel, time, mutedTime = false }: { checked: "empty" | "done" | "overdue"; title: string; category: string; timeLabel: string; time: string; mutedTime?: boolean }) {
  const check = checked === "done" ? taskCheckDoneIcon : checked === "overdue" ? taskCheckOverdueIcon : taskCheckEmptyIcon;
  const tone = category === "Покупки" ? "pink" : category === "Здоровье" ? "purple" : category === "Дом" ? "orange" : "green";
  return <div className="mini-task">
    <img className="mini-task-check" src={check} alt="" />
    <span className="mini-task-copy"><strong>{title}</strong><small className={`mini-task-category tone-${tone}`}>{category}</small></span>
    <span className={`mini-task-time${mutedTime ? " muted-time" : ""}`}><small>{timeLabel}</small><b>{time}</b></span>
  </div>;
}

function HomeTrainingCat() {
  return <div className="home-training-cat" aria-hidden="true">
    <img className="home-cat-shadow" src={homeCatShadow} />
    <img className="home-cat-body" src={homeCatBody} />
    <span className="home-cat-head"><img className="home-cat-head-shape" src={homeCatHead} /><img className="home-cat-eye" src={homeCatEye} /><img className="home-cat-star" src={homeCatStar} /><img className="home-cat-eye-mark home-cat-eye-mark-left" src={homeCatEyeMark} /><img className="home-cat-eye-mark home-cat-eye-mark-right" src={homeCatEyeMark2} /><img className="home-cat-ear" src={homeCatEar} /><img className="home-cat-foot home-cat-foot-left" src={homeCatFoot} /><img className="home-cat-foot home-cat-foot-right" src={homeCatFoot2} /></span>
  </div>;
}

function CalendarTrainingCat() {
  return <div className="calendar-training-cat" aria-hidden="true">
    <img className="calendar-cat-body" src={calendarCatBody} />
    <img className="calendar-cat-paw" src={calendarCatPaw} />
    <img className="calendar-cat-foot" src={calendarCatFoot} />
    <span className="calendar-cat-head"><img src={calendarCatHead} /></span>
    <img className="calendar-cat-eye" src={calendarCatEye} />
    <img className="calendar-cat-shadow" src={calendarCatShadow} />
  </div>;
}

function OnboardingFamily() {
  return <div className="mini-family-art">
    {[{ id: "general", label: "Общее", count: 4 }, { id: "health", label: "Здоровье", count: 2 }, { id: "home", label: "Дом", count: 2 }].map((category) => (
      <div className="mini-category-row" key={category.id}>
        <span className={`mini-category-icon tone-${categoryColors[category.id]}`}><CategoryIcon id={category.id} /></span>
        <span>{category.label}</span><b>{category.count}</b><img className="mini-dropdown" src={onboardingCategoryArrow} alt="" />
      </div>
    ))}
    <BlackFamilyTrainingCat /><WhiteFamilyTrainingCat />
    <span><img src={inviteLinkIcon} alt="" />Пригласить в семью</span>
  </div>;
}

function BlackFamilyTrainingCat() {
  return <div className="family-black-cat" aria-hidden="true">
    <img className="family-black-shadow" src={familyBlackShadow} />
    <span className="family-black-body"><img src={familyBlackBody} /></span>
    <span className="family-black-head"><span className="family-black-face"><img className="family-black-head-shape" src={familyBlackHead} /><span className="family-black-eye"><span><img src={familyBlackEye} /></span></span><span className="family-black-star"><span><img src={familyBlackStar} /></span></span><span className="family-black-mark-1-wrap"><span className="family-black-mark-1-rotated"><span className="family-black-mark-1-crop"><img src={familyBlackMark1} /></span></span></span><img className="family-black-mark family-black-mark-2" src={familyBlackMark2} /><img className="family-black-mark family-black-mark-3" src={familyBlackMark3} /><img className="family-black-ear" src={familyBlackEar} /></span></span>
    <img className="family-black-decor family-black-decor-1" src={familyBlackDecor1} /><img className="family-black-decor family-black-decor-2" src={familyBlackDecor2} /><img className="family-black-decor family-black-decor-3" src={familyBlackDecor3} /><img className="family-black-decor family-black-decor-4" src={familyBlackDecor4} /><img className="family-black-line" src={familyBlackDecorLine} /><img className="family-black-leg family-black-leg-1" src={familyBlackLeg1} /><img className="family-black-leg family-black-leg-2" src={familyBlackLeg2} />
    <span className="family-black-badge family-black-badge-general"><img src={familyBlackBadgeGeneral} /></span><span className="family-black-badge family-black-badge-health"><img src={familyBlackBadgeHealth} /></span><span className="family-black-badge family-black-badge-home"><img src={familyBlackBadgeHome} /></span>
  </div>;
}

function WhiteFamilyTrainingCat() {
  return <div className="family-white-cat" aria-hidden="true">
    <img className="family-white-paw" src={familyWhitePaw} /><img className="family-white-tail" src={familyWhiteTail} /><img className="family-white-body" src={familyWhiteBody} />
    <span className="family-white-head"><span className="family-white-face"><img className="family-white-head-shape" src={familyWhiteHead} /><img className="family-white-eye" src={familyWhiteEye} /><img className="family-white-star" src={familyWhiteStar} /><img className="family-white-eye-mark family-white-eye-mark-1" src={familyWhiteEyeMark} /><img className="family-white-eye-mark family-white-eye-mark-2" src={familyWhiteEyeMark} /><img className="family-white-ear family-white-ear-1" src={familyWhiteEar1} /><img className="family-white-ear family-white-ear-2" src={familyWhiteEar2} /><img className="family-white-dot family-white-dot-1" src={familyWhiteEyeDot} /><img className="family-white-dot family-white-dot-2" src={familyWhiteEyeDot} /><img className="family-white-dot family-white-dot-3" src={familyWhiteEyeDot2} /><img className="family-white-dot family-white-dot-4" src={familyWhiteEyeDot2} /></span></span>
    <img className="family-white-tail-mark" src={familyWhiteTailMark} /><img className="family-white-bow" src={familyWhiteBow} />
  </div>;
}

function OnboardingReminder() {
  return <div className="mini-reminder-scene">
    <div className="mini-reminder-art">
      <div className="mini-date-grid">
        <span><img src={onboardingDateDotPurple} alt="" />Без дедлайна</span>
        <span><img src={onboardingDateDotGreen} alt="" />Сегодня</span>
        <span><img src={onboardingDateDotPurple} alt="" />Завтра</span>
        <span className="mini-other-date"><img src={onboardingDateCalendar} alt="" />Другая дата</span>
      </div>
      <div className="mini-time"><img src={onboardingTimeClock} alt="" /><b>16:00</b></div>
      <div className="mini-reminder-toggle"><img src={bellIcon} alt="" />Напомнить<img className="mini-toggle-switch" src={onboardingToggle} alt="" /></div>
      <small>Напоминание придёт в день события</small>
    </div>
    <ReminderNotificationCat />
    <img className="reminder-head-shadow" src={reminderHeadShadow} alt="" />
    <img className="reminder-head" src={reminderHead} alt="" />
    <span className="reminder-arrow reminder-arrow-large"><img src={reminderHeadArrow} alt="" /></span>
    <span className="reminder-arrow reminder-arrow-small"><img src={reminderHeadArrowShort} alt="" /></span>
  </div>;
}

function ReminderNotificationCat() {
  return <div className="reminder-notification-cat" aria-hidden="true">
    <img className="notification-tail" src={reminderCatTail} />
    <img className="notification-body" src={reminderCatBody} />
    <img className="notification-leg" src={reminderCatLeg} />
    <img className="notification-paw" src={reminderCatPaw} />
    <span className="notification-cat-head"><img className="notification-head-shape" src={reminderCatHead} /><img className="notification-eye" src={reminderCatEye} /><img className="notification-star" src={reminderCatStar} /><img className="notification-eye-mark notification-eye-mark-left" src={reminderCatEyeMark} /><img className="notification-eye-mark notification-eye-mark-right" src={reminderCatEyeMark2} /><img className="notification-ear" src={reminderCatEar} /></span>
    <img className="notification-foot notification-foot-one" src={reminderCatFoot} />
    <img className="notification-foot notification-foot-two" src={reminderCatToe} />
    <img className="notification-foot notification-foot-three" src={reminderCatToe2} />
  </div>;
}

function TeaIllustration({ variant, className = "" }: { variant: "welcome" | "help"; className?: string }) {
  const assets = variant === "welcome"
    ? { body: welcomeBody, right: welcomeBranchRight, left: welcomeBranchLeft, head: welcomeHead, detail: welcomeDetail, floor: welcomeFloor, wave: welcomeWave, cup: welcomeCup }
    : { body: helpBody, right: helpBranchRight, left: helpBranchLeft, head: helpHead, detail: helpDetail, floor: helpFloor, wave: helpWave, cup: helpCup };
  return <div className={`tea-illustration tea-${variant} ${className}`} aria-hidden="true">
    <img className="tea-body" src={assets.body} />
    <span className="tea-branch tea-branch-right"><img src={assets.right} /></span>
    <span className="tea-branch tea-branch-left"><img src={assets.left} /></span>
    <span className="tea-head"><img src={assets.head} /></span>
    <span className="tea-detail"><img src={assets.detail} /></span>
    <img className="tea-wave" src={assets.wave} />
    <img className="tea-floor" src={assets.floor} />
    <img className="tea-cup" src={assets.cup} />
  </div>;
}

function NoFamilyScreen({ onBack }: { onBack: () => void }) {
  const botUrl = "https://t.me/easy_task_manager_bot";
  return <section className="no-family-screen"><TeaIllustration variant="welcome" /><h1>Добро пожаловать!</h1><p>Сначала создайте семью или присоединитесь к ней в боте.</p><a href={botUrl} onClick={(event) => { const openTelegramLink = window.Telegram?.WebApp?.openTelegramLink; if (openTelegramLink) { event.preventDefault(); openTelegramLink(botUrl); } }}>Открыть бот</a><button onClick={onBack}>Вернуться</button></section>;
}

function sortCategories(categories: Category[]): Category[] {
  const order = ["general", "health", "home", "shopping", "work"];
  return [...categories].sort((left, right) => {
    const leftIndex = order.indexOf(left.id);
    const rightIndex = order.indexOf(right.id);
    if (leftIndex < 0 && rightIndex < 0) return left.title.localeCompare(right.title, "ru");
    if (leftIndex < 0) return 1;
    if (rightIndex < 0) return -1;
    return leftIndex - rightIndex;
  });
}

function sortFormCategories(categories: Category[]): Category[] {
  const order = ["general", "health", "shopping", "work", "home"];
  return [...categories].sort((left, right) => {
    const leftIndex = order.indexOf(left.id);
    const rightIndex = order.indexOf(right.id);
    if (leftIndex < 0 && rightIndex < 0) return left.title.localeCompare(right.title, "ru");
    if (leftIndex < 0) return 1;
    if (rightIndex < 0) return -1;
    return leftIndex - rightIndex;
  });
}

function greeting() {
  const hour = Number(new Intl.DateTimeFormat("ru-RU", { hour: "2-digit", hourCycle: "h23", timeZone: "Europe/Moscow" }).format(new Date()));
  if (hour < 12) return "Доброе утро";
  if (hour < 18) return "Добрый день";
  return "Добрый вечер";
}

function useIsoToday() {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Moscow", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date());
}

function addIsoDays(value: string, days: number) {
  const [year, month, day] = value.split("-").map(Number);
  const result = new Date(Date.UTC(year, month - 1, day + days));
  return `${result.getUTCFullYear()}-${String(result.getUTCMonth() + 1).padStart(2, "0")}-${String(result.getUTCDate()).padStart(2, "0")}`;
}

function formatRuDate(value: string) {
  const [year, month, day] = value.split("-");
  return `${day}.${month}.${year}`;
}

function relativeDateLabel(value: string | null, today: string) {
  if (!value) return "";
  if (value < today) return "Вчера";
  if (value === today) return "Сегодня";
  if (value === addIsoDays(today, 1)) return "Завтра";
  return formatRuDate(value);
}

function initial(name: string) {
  return name.trim().charAt(0).toLocaleUpperCase("ru-RU") || "?";
}

createRoot(document.getElementById("root")!).render(<App />);
