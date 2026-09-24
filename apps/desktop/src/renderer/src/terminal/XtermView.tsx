import { useEffect, useRef } from "react";
import { Terminal } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import "@xterm/xterm/css/xterm.css";
import { TERMINAL_FONT_FAMILY, TERMINAL_FONT_SIZE, TERMINAL_THEME } from "./terminalTheme";

interface XtermViewProps {
  terminalId: string;
  active: boolean;
}

export function XtermView({ terminalId, active }: XtermViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const termRef = useRef<Terminal | null>(null);
  const fitRef = useRef<FitAddon | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const term = new Terminal({
      cursorBlink: true,
      cursorStyle: "bar",
      cursorWidth: 2,
      fontSize: TERMINAL_FONT_SIZE,
      lineHeight: 1,
      fontFamily: TERMINAL_FONT_FAMILY,
      fontWeight: "400",
      fontWeightBold: "600",
      theme: TERMINAL_THEME,
      scrollback: 8000,
      drawBoldTextInBrightColors: true,
      minimumContrastRatio: 1,
    });

    const fitAddon = new FitAddon();
    term.loadAddon(fitAddon);
    term.open(container);

    term.onData((data) => {
      void window.desktop.terminal.write(terminalId, data);
    });

    const unsub = window.desktop.terminal.onOutput((event) => {
      if (event.terminalId !== terminalId) return;
      if (event.type === "stdout" || event.type === "stderr") {
        term.write(event.data);
      }
    });

    let resizeFrame = 0;
    const fitTerminal = () => {
      cancelAnimationFrame(resizeFrame);
      resizeFrame = requestAnimationFrame(() => {
        const el = containerRef.current;
        if (!el || el.clientWidth < 2 || el.clientHeight < 2) return;
        fitAddon.fit();
        void window.desktop.terminal.resize(terminalId, term.cols, term.rows);
      });
    };

    const observer = new ResizeObserver(() => fitTerminal());
    observer.observe(container);

    // Layout may not be ready on first paint — fit again after mount.
    fitTerminal();
    const retryFit = window.setTimeout(() => fitTerminal(), 50);
    const retryFit2 = window.setTimeout(() => fitTerminal(), 200);

    term.focus();
    void window.desktop.terminal.replay(terminalId);

    termRef.current = term;
    fitRef.current = fitAddon;

    return () => {
      window.clearTimeout(retryFit);
      window.clearTimeout(retryFit2);
      cancelAnimationFrame(resizeFrame);
      unsub();
      observer.disconnect();
      term.dispose();
      termRef.current = null;
      fitRef.current = null;
    };
  }, [terminalId]);

  useEffect(() => {
    if (!active) return;
    const term = termRef.current;
    const fit = fitRef.current;
    const container = containerRef.current;
    if (!term || !fit || !container) return;

    requestAnimationFrame(() => {
      if (container.clientWidth >= 2 && container.clientHeight >= 2) {
        fit.fit();
        void window.desktop.terminal.resize(terminalId, term.cols, term.rows);
      }
      term.focus();
    });
  }, [active, terminalId]);

  return <div ref={containerRef} className="terminal-xterm-host" />;
}
