/* ==========================================================================
   我的知识小栈 · 全站交互
   原生 JavaScript，无框架依赖：
   主题切换 / 移动端导航 / 搜索弹窗 / 表单确认 / 复制 / 字符计数 / 提示
   ========================================================================== */
(function () {
  "use strict";

  const $ = (selector, scope) => (scope || document).querySelector(selector);
  const $$ = (selector, scope) => Array.from((scope || document).querySelectorAll(selector));
  const root = document.documentElement;
  const THEME_KEY = "knowledge-stack-theme";
  const csrfToken = $('meta[name="csrf-token"]')?.content || "";

  // ---------- 主题 ----------
  const themeButton = $("[data-theme-toggle]");
  const systemDark = window.matchMedia("(prefers-color-scheme: dark)");

  function applyTheme(theme, persist) {
    root.dataset.theme = theme;
    if (themeButton) themeButton.setAttribute("aria-pressed", theme === "dark" ? "true" : "false");
    const meta = $('meta[name="theme-color"]');
    if (meta) meta.setAttribute("content", theme === "dark" ? "#101613" : "#f6f4ee");
    if (persist) {
      try { localStorage.setItem(THEME_KEY, theme); } catch (error) { /* 隐私模式忽略 */ }
    }
  }

  applyTheme(root.dataset.theme || (systemDark.matches ? "dark" : "light"), false);

  if (themeButton) {
    themeButton.addEventListener("click", function () {
      const next = root.dataset.theme === "dark" ? "light" : "dark";
      applyTheme(next, true);
    });
  }

  systemDark.addEventListener?.("change", function (event) {
    let stored = null;
    try { stored = localStorage.getItem(THEME_KEY); } catch (error) { /* ignore */ }
    if (!stored) applyTheme(event.matches ? "dark" : "light", false);
  });

  // ---------- 页头滚动阴影 ----------
  const header = $("[data-header]");
  const backToTop = $("[data-back-to-top]");
  function onScroll() {
    const y = window.scrollY || window.pageYOffset;
    header?.classList.toggle("is-scrolled", y > 8);
    backToTop?.classList.toggle("is-visible", y > 520);
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
  backToTop?.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));

  // ---------- 移动端导航 ----------
  const navToggle = $("[data-nav-toggle]");
  const nav = $("#site-nav");

  function setNav(open) {
    if (!nav || !navToggle) return;
    nav.classList.toggle("is-open", open);
    header?.classList.toggle("nav-open", open);
    navToggle.setAttribute("aria-expanded", open ? "true" : "false");
    navToggle.setAttribute("aria-label", open ? "关闭导航" : "打开导航");
  }

  navToggle?.addEventListener("click", function () {
    setNav(!nav.classList.contains("is-open"));
  });
  $$("#site-nav a").forEach((link) => link.addEventListener("click", () => setNav(false)));
  window.addEventListener("resize", function () {
    if (window.innerWidth > 860) setNav(false);
  });

  // ---------- 搜索弹窗 ----------
  const searchDialog = $("#search-modal");
  const openSearchButtons = $$("[data-open-search]");
  const closeSearchButton = $("[data-close-search]");
  const searchInput = $("#global-search-input");

  function openSearch() {
    if (!searchDialog) return;
    if (typeof searchDialog.showModal === "function") searchDialog.showModal();
    else searchDialog.setAttribute("open", "");
    window.setTimeout(() => searchInput?.focus(), 60);
  }
  function closeSearch() {
    if (!searchDialog) return;
    if (typeof searchDialog.close === "function") searchDialog.close();
    else searchDialog.removeAttribute("open");
  }

  openSearchButtons.forEach((button) => button.addEventListener("click", openSearch));
  closeSearchButton?.addEventListener("click", closeSearch);
  searchDialog?.addEventListener("click", function (event) {
    if (event.target === searchDialog) closeSearch();
  });

  document.addEventListener("keydown", function (event) {
    const target = event.target;
    const typing = target instanceof HTMLElement && (
      target.matches("input, textarea, select") || target.isContentEditable
    );
    if (event.key === "/" && !typing && !event.metaKey && !event.ctrlKey && !event.altKey) {
      event.preventDefault();
      openSearch();
    }
    if (event.key === "Escape") {
      setNav(false);
      $$(".user-menu[open]").forEach((menu) => menu.removeAttribute("open"));
    }
  });

  // ---------- Flash 提示 ----------
  $$("[data-flash]").forEach(function (flash) {
    const timer = window.setTimeout(() => dismissFlash(flash), 5200);
    $("[data-close-flash]", flash)?.addEventListener("click", function () {
      window.clearTimeout(timer);
      dismissFlash(flash);
    });
  });

  function dismissFlash(flash) {
    flash.classList.add("is-leaving");
    window.setTimeout(() => flash.remove(), 260);
  }

  function showToast(message) {
    let toast = $(".copy-toast");
    if (!toast) {
      toast = document.createElement("div");
      toast.className = "copy-toast";
      toast.setAttribute("role", "status");
      toast.setAttribute("aria-live", "polite");
      document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.classList.add("is-visible");
    window.clearTimeout(showToast.timer);
    showToast.timer = window.setTimeout(() => toast.classList.remove("is-visible"), 2400);
  }

  // ---------- 表单二次确认 ----------
  $$("form[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      if (form.dataset.confirmed === "1") return;
      if (!window.confirm(form.dataset.confirm || "确认执行该操作吗？")) {
        event.preventDefault();
        return;
      }
      form.dataset.confirmed = "1";
    });
  });

  // ---------- 密码显隐 ----------
  $$("[data-password-toggle]").forEach(function (button) {
    button.addEventListener("click", function () {
      const input = $(button.dataset.passwordToggle);
      if (!input) return;
      const showing = input.type === "text";
      input.type = showing ? "password" : "text";
      button.setAttribute("aria-label", showing ? "显示密码" : "隐藏密码");
      button.style.color = showing ? "" : "var(--brand)";
    });
  });

  // ---------- 字符计数 ----------
  $$("[data-char-count-for]").forEach(function (output) {
    const input = document.getElementById(output.dataset.charCountFor);
    if (!input) return;
    const update = function () { output.textContent = String(input.value.length); };
    input.addEventListener("input", update);
    update();
  });

  // ---------- 复制 ----------
  async function copyText(text) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (error) {
      const area = document.createElement("textarea");
      area.value = text;
      area.style.position = "fixed";
      area.style.opacity = "0";
      document.body.appendChild(area);
      area.select();
      let ok = false;
      try { ok = document.execCommand("copy"); } catch (err) { ok = false; }
      area.remove();
      return ok;
    }
  }

  $$("[data-copy]").forEach(function (button) {
    button.addEventListener("click", async function () {
      const ok = await copyText(button.dataset.copy || "");
      showToast(ok ? (button.dataset.copyLabel || "已复制到剪贴板") : "复制失败，请手动选择");
    });
  });

  $$("[data-copy-current]").forEach(function (button) {
    button.addEventListener("click", async function () {
      const ok = await copyText(window.location.href);
      showToast(ok ? "文章链接已复制" : "复制失败，请手动复制地址栏");
    });
  });

  // ---------- 后台内联编辑 ----------
  $$("[data-toggle-edit]").forEach(function (button) {
    button.addEventListener("click", function () {
      const target = document.getElementById(button.dataset.toggleEdit);
      if (!target) return;
      const willShow = target.hidden;
      target.hidden = !willShow;
      button.setAttribute("aria-expanded", willShow ? "true" : "false");
      if (willShow) target.querySelector("input:not([type=color])")?.focus();
    });
  });

  // ---------- 登录演示账号一键填充 ----------
  $$("[data-fill-login]").forEach(function (button) {
    button.addEventListener("click", function () {
      const identifier = $("#identifier");
      const password = $("#password");
      if (!identifier || !password) return;
      identifier.value = button.dataset.username || "";
      password.value = button.dataset.password || "";
      showToast("演示账号已填入，点击「登录」继续");
      identifier.focus();
    });
  });

  // ---------- 上传文件自动提交 ----------
  $$("[data-auto-submit]").forEach(function (input) {
    input.addEventListener("change", function () {
      if (input.files && input.files.length) input.form?.requestSubmit();
    });
  });

  // ---------- 封面文件本地预览 ----------
  const coverInput = $("[data-cover-file]");
  const coverPreview = $("[data-cover-preview]");
  coverInput?.addEventListener("change", function () {
    const file = coverInput.files?.[0];
    if (!file || !coverPreview) return;
    if (!file.type.startsWith("image/")) return;
    const url = URL.createObjectURL(file);
    coverPreview.innerHTML = "";
    const image = document.createElement("img");
    image.src = url;
    image.alt = "封面预览";
    image.onload = () => URL.revokeObjectURL(url);
    coverPreview.appendChild(image);
  });

  // ---------- 用户菜单点击外部关闭 ----------
  document.addEventListener("click", function (event) {
    $$(".user-menu[open]").forEach(function (menu) {
      if (!menu.contains(event.target)) menu.removeAttribute("open");
    });
  });

  // ---------- 全局暴露 ----------
  window.KnowledgeStack = { $, $$, csrfToken, showToast, copyText };
})();
