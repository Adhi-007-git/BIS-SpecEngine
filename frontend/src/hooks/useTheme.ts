// Deprecated: Single Warm Beige Theme is strictly enforced.
// This utility ensures any legacy 'dark' class is removed from documentElement.
import { useEffect } from 'react';

export const useTheme = () => {
  useEffect(() => {
    try {
      document.documentElement.classList.remove('dark');
      localStorage.removeItem('bis_theme');
    } catch {
      // ignore
    }
  }, []);

  return { isDark: false };
};
