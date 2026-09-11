import React, { createContext, useContext, useEffect, useState } from 'react';

export type Theme = 'night' | 'white';

interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
  setTheme: (theme: Theme) => void;
  isNight: boolean;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const THEME_STORAGE_KEY = 'docuagent_theme';

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setThemeState] = useState<Theme>(() => {
    try {
      const saved = localStorage.getItem(THEME_STORAGE_KEY);
      if (saved === 'white' || saved === 'night') return saved;
      // Default to night mode
      return 'night';
    } catch {
      return 'night';
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem(THEME_STORAGE_KEY, theme);
    } catch (e) {
      console.warn('Could not save theme to localStorage', e);
    }

    const root = document.documentElement;
    root.setAttribute('data-theme', theme);

    if (theme === 'white') {
      root.classList.add('theme-white');
      root.classList.remove('theme-night', 'dark');
    } else {
      root.classList.add('theme-night', 'dark');
      root.classList.remove('theme-white');
    }
  }, [theme]);

  const toggleTheme = () => {
    setThemeState((prev) => (prev === 'night' ? 'white' : 'night'));
  };

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
  };

  return (
    <ThemeContext.Provider
      value={{
        theme,
        toggleTheme,
        setTheme,
        isNight: theme === 'night',
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};
