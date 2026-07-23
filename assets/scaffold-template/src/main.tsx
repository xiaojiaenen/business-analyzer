import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { HashRouter } from "react-router-dom";
import { App } from "./App";
import "reacticle/styles.css";
import "./print-overrides.css";
import "./mermaid-overrides.css";

// 入口：HashRouter 支持离线 file:// 打开，路由切换不依赖服务端。
// 所有文档页面共享这一个入口，主题在各 Page 组件内通过 <ThemeProvider> 声明。

// === file:// 锚点跳转修复 ===
// reacticle TOC 用原生 <a href="#section-xx"> 锚点跳转。
// 在 file:// 协议下，浏览器把每个 file:// URL 当作独立 origin，
// 导致 "Unsafe attempt to load URL ... 'file:' URLs are treated as unique security origins" 错误。
// 此处注入全局点击拦截：拦截 a[href^="#"] 点击，改为 scrollIntoView()。
if (typeof document !== "undefined") {
  document.addEventListener("click", (e) => {
    const target = e.target as Element;
    const anchor = target.closest("a[href^='#']") as HTMLAnchorElement | null;
    if (!anchor) return;
    const hash = anchor.getAttribute("href");
    if (!hash || hash === "#") return;
    const id = hash.slice(1);
    const el = document.getElementById(id);
    if (el) {
      e.preventDefault();
      el.scrollIntoView({ behavior: "smooth", block: "start" });
      // 不改 location.hash，避免触发 file:// 安全错误
    }
  });
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <HashRouter>
      <App />
    </HashRouter>
  </StrictMode>
);
