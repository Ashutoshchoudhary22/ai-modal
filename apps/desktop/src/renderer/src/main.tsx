import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./index.css";
import { useCompletionStore } from "./features/completion/completionStore";

if (import.meta.env.DEV) {
  (window as Window & { __COMPLETION_E2E__?: typeof useCompletionStore }).__COMPLETION_E2E__ =
    useCompletionStore;
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
