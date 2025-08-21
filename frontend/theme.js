/**
 * Theme Manager - Handles dark/light mode switching with persistence
 * 
 * Features:
 * - Detects and respects system preferences (prefers-color-scheme)
 * - Persists user preference in localStorage
 * - Provides smooth transitions between themes
 * - Accessible keyboard navigation and screen reader support
 */

class ThemeManager {
    constructor() {
        this.STORAGE_KEY = 'theme-preference';
        this.themeToggle = null;
        this.themeLabel = null;
        this.currentTheme = 'light';
        this.systemPreference = null;
    }

    /**
     * Initialize the theme manager
     */
    init() {
        // Get DOM elements
        this.themeToggle = document.getElementById('themeToggle');
        this.themeLabel = document.getElementById('themeLabel');
        
        if (!this.themeToggle) {
            console.warn('Theme toggle button not found');
            return;
        }

        // Detect system preference
        this.detectSystemPreference();
        
        // Load saved preference or use system preference
        this.loadTheme();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Listen for system preference changes
        this.watchSystemPreference();
    }

    /**
     * Detect the system color scheme preference
     */
    detectSystemPreference() {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            this.systemPreference = 'dark';
        } else {
            this.systemPreference = 'light';
        }
    }

    /**
     * Watch for changes in system color scheme preference
     */
    watchSystemPreference() {
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            
            // Modern browsers
            if (mediaQuery.addEventListener) {
                mediaQuery.addEventListener('change', (e) => {
                    this.systemPreference = e.matches ? 'dark' : 'light';
                    
                    // If no saved preference, follow system
                    const savedTheme = localStorage.getItem(this.STORAGE_KEY);
                    if (!savedTheme || savedTheme === 'system') {
                        this.setTheme(this.systemPreference, false);
                    }
                });
            } else if (mediaQuery.addListener) {
                // Legacy browsers
                mediaQuery.addListener((e) => {
                    this.systemPreference = e.matches ? 'dark' : 'light';
                    
                    const savedTheme = localStorage.getItem(this.STORAGE_KEY);
                    if (!savedTheme || savedTheme === 'system') {
                        this.setTheme(this.systemPreference, false);
                    }
                });
            }
        }
    }

    /**
     * Load theme from localStorage or system preference
     */
    loadTheme() {
        const savedTheme = localStorage.getItem(this.STORAGE_KEY);
        
        if (savedTheme && savedTheme !== 'system') {
            // Use saved preference
            this.setTheme(savedTheme, false);
        } else {
            // Use system preference
            this.setTheme(this.systemPreference, false);
        }
    }

    /**
     * Set up event listeners for theme toggle
     */
    setupEventListeners() {
        // Click event for theme toggle
        this.themeToggle.addEventListener('click', () => {
            this.toggleTheme();
        });

        // Keyboard accessibility - Space and Enter keys
        this.themeToggle.addEventListener('keydown', (e) => {
            if (e.key === ' ' || e.key === 'Enter') {
                e.preventDefault();
                this.toggleTheme();
            }
        });
    }

    /**
     * Toggle between light and dark themes
     */
    toggleTheme() {
        const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.setTheme(newTheme, true);
    }

    /**
     * Set the theme and update UI
     * @param {string} theme - 'light' or 'dark'
     * @param {boolean} save - Whether to save preference to localStorage
     */
    setTheme(theme, save = true) {
        this.currentTheme = theme;
        
        // Update data attribute on body
        document.documentElement.setAttribute('data-theme', theme);
        
        // Update toggle button state
        this.updateToggleState(theme);
        
        // Update label
        this.updateLabel(theme);
        
        // Save preference if requested
        if (save) {
            localStorage.setItem(this.STORAGE_KEY, theme);
        }
        
        // Dispatch custom event for other components to listen to
        window.dispatchEvent(new CustomEvent('themechange', { 
            detail: { theme } 
        }));
    }

    /**
     * Update the toggle button's visual and accessibility state
     * @param {string} theme - Current theme
     */
    updateToggleState(theme) {
        const isDark = theme === 'dark';
        
        // Update ARIA attributes for accessibility
        this.themeToggle.setAttribute('aria-checked', isDark.toString());
        this.themeToggle.setAttribute('aria-label', 
            isDark ? 'Switch to light mode' : 'Switch to dark mode'
        );
    }

    /**
     * Update the theme label text
     * @param {string} theme - Current theme
     */
    updateLabel(theme) {
        if (this.themeLabel) {
            this.themeLabel.textContent = theme === 'dark' ? 'Dark' : 'Light';
        }
    }

    /**
     * Get the current theme
     * @returns {string} Current theme ('light' or 'dark')
     */
    getCurrentTheme() {
        return this.currentTheme;
    }

    /**
     * Clear saved preference and revert to system preference
     */
    clearPreference() {
        localStorage.removeItem(this.STORAGE_KEY);
        this.setTheme(this.systemPreference, false);
    }
}

// Initialize theme manager when DOM is ready
const themeManager = new ThemeManager();

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => themeManager.init());
} else {
    // DOM is already loaded
    themeManager.init();
}

// Export for use in other modules if needed
window.themeManager = themeManager;