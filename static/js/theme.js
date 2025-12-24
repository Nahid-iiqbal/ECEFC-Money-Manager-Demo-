(function() {
    'use strict';
    
    const THEME_KEY = 'feinbuddy_theme';
    const themeToggle = document.getElementById('themeToggle');
    const body = document.body;
    
    function getStoredTheme() {
        return localStorage.getItem(THEME_KEY) || 'light';
    }
    
    function setStoredTheme(theme) {
        localStorage.setItem(THEME_KEY, theme);
    }
    
    function applyTheme(theme) {
        body.setAttribute('data-theme', theme);
        updateToggleButton(theme);
    }
    
    function updateToggleButton(theme) {
        const icon = themeToggle.querySelector('.theme-icon');
        const label = themeToggle.querySelector('.theme-label');
        
        if (theme === 'dark') {
            icon.textContent = '☀️';
            label.textContent = 'Normal Mode';
            themeToggle.setAttribute('aria-label', 'Switch to Normal Mode');
        } else {
            icon.textContent = '🌙';
            label.textContent = 'Upside Down';
            themeToggle.setAttribute('aria-label', 'Switch to Upside Down Mode');
        }
    }
    
    function toggleTheme() {
        const currentTheme = body.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        applyTheme(newTheme);
        setStoredTheme(newTheme);
        
        body.style.transition = 'background-color 0.3s ease, color 0.3s ease';
        setTimeout(() => {
            body.style.transition = '';
        }, 300);
    }
    
    function init() {
        const storedTheme = getStoredTheme();
        applyTheme(storedTheme);
        
        if (themeToggle) {
            themeToggle.addEventListener('click', toggleTheme);
        }
        
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');
        if (!localStorage.getItem(THEME_KEY)) {
            applyTheme(prefersLight.matches ? 'dark' : 'light');
        }
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
