import { useEffect } from "react";
import { Routes, Route, useLocation } from "react-router-dom";
import { IndexPage } from "./pages/IndexPage";
import { SampleDoc } from "./pages/SampleDoc";
import { PrintAllPage } from "./pages/PrintAllPage";

// 路由切换时滚动到顶部
function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
}

export function App() {
  return (
    <>
      <ScrollToTop />
      <Routes>
        <Route path="/" element={<IndexPage />} />
        <Route path="/sample" element={<SampleDoc />} />
        {/* 打印专用路由：渲染所有文档到一页，用于导出 PDF。详见 PrintAllPage.tsx */}
        <Route path="/print-all" element={<PrintAllPage />} />
        {/*
          Agent 在此添加更多文档路由，例如：
          <Route path="/business-overview" element={<BusinessOverview />} />
          <Route path="/domain-model" element={<DomainModel />} />
          <Route path="/glossary" element={<Glossary />} />
        */}
      </Routes>
    </>
  );
}
