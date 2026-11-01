/* ==========================================================================
   Markdown 编辑器交互
   - 工具栏：加粗、标题、列表、引用、代码块、链接、表格
   - 实时预览：后端渲染 + bleach 白名单过滤，前端只负责展示
   - 图片：工具栏、粘贴、拖拽上传后自动插入 Markdown
   ========================================================================== */
(function () {
  "use strict";

  const workbench = document.querySelector("[data-editor]");
  if (!workbench) return;

  const textarea = workbench.querySelector(".editor-textarea");
  const preview = workbench.querySelector("[data-preview-content]");
  const previewStatus = workbench.querySelector("[data-preview-status]");
  const previewUrl = textarea?.dataset.previewUrl;
  const uploadUrl = workbench.dataset.uploadUrl;
  const imageInput = document.querySelector("[data-image-input]");
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";
  const wordCount = document.querySelector("[data-word-count]");
  const readingTime = document.querySelector("[data-reading-time]");
  const titleInput = document.querySelector("#title");
  const titleCount = document.querySelector("[data-title-count]");
  const form = workbench.closest("form");

  if (!textarea || !preview) return;

  let previewTimer;
  let previewSequence = 0;
  let dirty = false;
  let submitting = false;
  const initialValue = textarea.value;

  // ---------- 字数与阅读时长 ----------
  function updateCounts() {
    const value = textarea.value;
    const characters = value.replace(/\s/g, "").length;
    if (wordCount) wordCount.textContent = String(characters);
    if (readingTime) readingTime.textContent = String(Math.max(1, Math.ceil(characters / 400)));
  }

  function updateTitleCount() {
    if (titleInput && titleCount) titleCount.textContent = String(titleInput.value.length);
  }

  updateCounts();
  updateTitleCount();
  titleInput?.addEventListener("input", updateTitleCount);

  // ---------- 文本插入辅助 ----------
  function replaceSelection(before, after, placeholder) {
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selected = textarea.value.slice(start, end) || placeholder || "";
    const replacement = before + selected + after;
    textarea.setRangeText(replacement, start, end, "end");
    if (!textarea.value.slice(start, end).length) {
      textarea.setSelectionRange(start + before.length, start + before.length + selected.length);
    }
    textarea.focus();
    textarea.dispatchEvent(new Event("input", { bubbles: true }));
  }

  function prefixLines(prefix) {
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const before = textarea.value.lastIndexOf("\n", start - 1) + 1;
    let after = textarea.value.indexOf("\n", end);
    if (after === -1) after = textarea.value.length;
    const block = textarea.value.slice(before, after);
    const lines = block.split("\n");
    const allPrefixed = lines.every((line) => line.startsWith(prefix));
    const next = lines
      .map((line) => (allPrefixed ? line.slice(prefix.length) : prefix + line))
      .join("\n");
    textarea.setRangeText(next, before, after, "select");
    textarea.focus();
    textarea.dispatchEvent(new Event("input", { bubbles: true }));
  }

  function insertBlock(text) {
    const start = textarea.selectionStart;
    const needsLeading = start > 0 && textarea.value[start - 1] !== "\n";
    const content = (needsLeading ? "\n" : "") + text + (text.endsWith("\n") ? "" : "\n");
    textarea.setRangeText(content, textarea.selectionStart, textarea.selectionEnd, "end");
    textarea.focus();
    textarea.dispatchEvent(new Event("input", { bubbles: true }));
  }

  function insertImageMarkdown(url, name) {
    const alt = (name || "图片").replace(/[\[\]]/g, "");
    insertBlock(`![${alt}](${url})\n`);
  }

  // ---------- 工具栏 ----------
  const toolbar = workbench.closest(".editor-panel")?.querySelector(".editor-toolbar");
  toolbar?.addEventListener("click", function (event) {
    const button = event.target.closest("button");
    if (!button) return;
    if (button.dataset.mdWrap !== undefined) {
      replaceSelection(button.dataset.mdWrap, button.dataset.mdWrap, "文字");
    } else if (button.dataset.mdPrefix !== undefined) {
      prefixLines(button.dataset.mdPrefix);
    } else if (button.dataset.mdBlock === "code") {
      const selected = textarea.value.slice(textarea.selectionStart, textarea.selectionEnd);
      insertBlock("```\n" + (selected || "在这里写代码") + "\n```\n");
    } else if (button.hasAttribute("data-md-link")) {
      const selected = textarea.value.slice(textarea.selectionStart, textarea.selectionEnd);
      replaceSelection("[", "](https://example.com)", selected || "链接文字");
    } else if (button.hasAttribute("data-md-table")) {
      insertBlock("| 表头一 | 表头二 |\n| --- | --- |\n| 内容 | 内容 |\n");
    } else if (button.hasAttribute("data-insert-image")) {
      imageInput?.click();
    } else if (button.hasAttribute("data-editor-preview-toggle")) {
      const onlyPreview = workbench.classList.toggle("is-preview-only");
      button.setAttribute("aria-pressed", onlyPreview ? "true" : "false");
      button.innerHTML = onlyPreview ? "编辑" : "预览";
    }
  });

  textarea.addEventListener("keydown", function (event) {
    const mod = event.ctrlKey || event.metaKey;
    if (!mod) return;
    if (event.key.toLowerCase() === "b") {
      event.preventDefault();
      replaceSelection("**", "**", "加粗文字");
    } else if (event.key.toLowerCase() === "i") {
      event.preventDefault();
      replaceSelection("*", "*", "斜体文字");
    }
  });

  // ---------- 实时预览 ----------
  function setPreviewStatus(text, isError) {
    if (!previewStatus) return;
    previewStatus.textContent = text;
    previewStatus.style.color = isError ? "var(--danger)" : "var(--success)";
  }

  async function refreshPreview() {
    if (!previewUrl) return;
    const content = textarea.value;
    if (!content.trim()) {
      preview.innerHTML = '<p class="editor-preview__empty">在左侧输入 Markdown，这里会实时渲染。</p>';
      setPreviewStatus("等待输入", false);
      return;
    }
    const sequence = ++previewSequence;
    setPreviewStatus("渲染中…", false);
    try {
      const response = await fetch(previewUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
          "X-Requested-With": "XMLHttpRequest",
        },
        body: JSON.stringify({ content }),
      });
      const data = await response.json();
      if (sequence !== previewSequence) return;
      if (!response.ok || !data.ok) throw new Error(data.message || "预览失败");
      preview.innerHTML = data.html || '<p class="editor-preview__empty">暂无内容。</p>';
      setPreviewStatus("已同步", false);
    } catch (error) {
      if (sequence !== previewSequence) return;
      setPreviewStatus("预览暂不可用", true);
      preview.innerHTML = '<p class="editor-preview__empty">预览请求失败，请检查登录状态后重试。正文不会丢失。</p>';
    }
  }

  textarea.addEventListener("input", function () {
    dirty = true;
    updateCounts();
    window.clearTimeout(previewTimer);
    previewTimer = window.setTimeout(refreshPreview, 320);
  });

  if (textarea.value.trim()) refreshPreview();

  // ---------- 图片上传 ----------
  async function uploadFile(file) {
    if (!file) return;
    if (!uploadUrl) return;
    if (!file.type.startsWith("image/")) {
      window.KnowledgeStack?.showToast("请选择图片文件。");
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      window.KnowledgeStack?.showToast("图片不能超过 5MB。");
      return;
    }
    setPreviewStatus("图片上传中…", false);
    const body = new FormData();
    body.append("file", file);
    try {
      const response = await fetch(uploadUrl, {
        method: "POST",
        headers: { "X-CSRFToken": csrfToken, "X-Requested-With": "XMLHttpRequest" },
        body,
      });
      const data = await response.json();
      if (!response.ok || !data.ok) throw new Error(data.message || "上传失败");
      insertImageMarkdown(data.url, data.name);
      window.KnowledgeStack?.showToast("图片已上传并插入正文");
      setPreviewStatus("图片已插入", false);
    } catch (error) {
      window.KnowledgeStack?.showToast(error.message || "图片上传失败");
      setPreviewStatus("图片上传失败", true);
    }
  }

  imageInput?.addEventListener("change", function () {
    const file = imageInput.files?.[0];
    uploadFile(file);
    imageInput.value = "";
  });

  textarea.addEventListener("paste", function (event) {
    const items = Array.from(event.clipboardData?.items || []);
    const imageItem = items.find((item) => item.type.startsWith("image/"));
    if (!imageItem) return;
    const file = imageItem.getAsFile();
    if (!file) return;
    event.preventDefault();
    uploadFile(file);
  });

  textarea.addEventListener("dragover", function (event) {
    if (Array.from(event.dataTransfer?.items || []).some((item) => item.type.startsWith("image/"))) {
      event.preventDefault();
      textarea.classList.add("is-dragover");
    }
  });
  textarea.addEventListener("dragleave", () => textarea.classList.remove("is-dragover"));
  textarea.addEventListener("drop", function (event) {
    const file = Array.from(event.dataTransfer?.files || []).find((item) => item.type.startsWith("image/"));
    if (!file) return;
    event.preventDefault();
    textarea.classList.remove("is-dragover");
    uploadFile(file);
  });

  // ---------- 离开提醒 ----------
  form?.addEventListener("submit", function () {
    submitting = true;
  });
  window.addEventListener("beforeunload", function (event) {
    if (!submitting && dirty && textarea.value !== initialValue) {
      event.preventDefault();
      event.returnValue = "";
    }
  });
})();
