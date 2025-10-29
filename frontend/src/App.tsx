import { useCallback, useState } from "react";

import Home from "./components/Home";
import { LandingPage } from "./components/LandingPage";
import type { ColorScheme } from "./hooks/useColorScheme";
import { useColorScheme } from "./hooks/useColorScheme";

export default function App() {
  const { scheme, setScheme } = useColorScheme();
  const [showAdmin, setShowAdmin] = useState(false);

  const handleThemeChange = useCallback(
    (value: ColorScheme) => {
      setScheme(value);
    },
    [setScheme],
  );

  // Admin mode can be toggled with keyboard shortcut (Ctrl+Shift+A)
  useCallback(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.shiftKey && e.key === "A") {
        setShowAdmin((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return showAdmin ? (
    <Home scheme={scheme} onThemeChange={handleThemeChange} />
  ) : (
    <LandingPage scheme={scheme} onThemeChange={handleThemeChange} />
  );
}

