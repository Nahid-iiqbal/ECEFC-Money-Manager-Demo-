/* ============================================
   PROFESSIONAL NAVBAR SCROLL EFFECTS
   ============================================
   
   Purpose: Enhance sticky navbar with scroll-based visual feedback
   
   Features:
   - Adds 'scrolled' class when user scrolls down
   - Debounced for performance (60fps target)
   - Intersection Observer for efficient detection
   - No layout shifts or jank
   
   Why JavaScript is needed:
   - CSS :stuck pseudo-class has poor browser support
   - We want dynamic shadow/style changes based on scroll position
   - Provides smooth, performant transitions
   ============================================ */

(function() {
    'use strict';
    
    // Configuration
    const SCROLL_THRESHOLD = 50; // Pixels scrolled before triggering 'scrolled' class
    const DEBOUNCE_DELAY = 10; // Milliseconds to wait before processing scroll
    
    // Get navbar element
    const navbar = document.getElementById('mainNav');
    
    // Exit if navbar doesn't exist (e.g., logged out pages)
    if (!navbar) return;
    
    // Track last scroll position to prevent unnecessary updates
    let lastScrollY = window.scrollY;
    let ticking = false; // RequestAnimationFrame ticking flag
    
    /**
     * Update navbar appearance based on scroll position
     * Uses requestAnimationFrame for smooth 60fps updates
     */
    function updateNavbar() {
        const scrollY = window.scrollY;
        
        // Add 'scrolled' class when scrolled past threshold
        if (scrollY > SCROLL_THRESHOLD) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
        
        // Update last position
        lastScrollY = scrollY;
        ticking = false;
    }
    
    /**
     * Debounced scroll handler
     * Requests animation frame only when needed for performance
     */
    function onScroll() {
        if (!ticking) {
            window.requestAnimationFrame(updateNavbar);
            ticking = true;
        }
    }
    
    /**
     * Alternative: Intersection Observer method (more modern)
     * Detects when a sentinel element enters/exits viewport
     * More efficient than scroll events for simple threshold detection
     */
    function initIntersectionObserver() {
        // Create a sentinel element at the top of the page
        const sentinel = document.createElement('div');
        sentinel.style.position = 'absolute';
        sentinel.style.top = '0';
        sentinel.style.height = `${SCROLL_THRESHOLD}px`;
        sentinel.style.width = '1px';
        sentinel.style.pointerEvents = 'none';
        sentinel.style.visibility = 'hidden';
        document.body.insertBefore(sentinel, document.body.firstChild);
        
        // Observer options
        const observerOptions = {
            threshold: 0,
            rootMargin: '0px'
        };
        
        // Create observer
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                // When sentinel exits viewport (scrolled down), add class
                if (!entry.isIntersecting) {
                    navbar.classList.add('scrolled');
                } else {
                    navbar.classList.remove('scrolled');
                }
            });
        }, observerOptions);
        
        // Start observing
        observer.observe(sentinel);
    }
    
    /**
     * Initialize navbar behavior
     * Choose between scroll event or Intersection Observer
     */
    function init() {
        // Check initial scroll position
        updateNavbar();
        
        // Use Intersection Observer if supported (better performance)
        if ('IntersectionObserver' in window) {
            initIntersectionObserver();
        } else {
            // Fallback to scroll event for older browsers
            window.addEventListener('scroll', onScroll, { passive: true });
        }
        
        // Update on window resize (in case navbar height changes)
        let resizeTimer;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(updateNavbar, 100);
        }, { passive: true });
    }
    
    /**
     * Keyboard navigation enhancement
     * Improve focus visibility when tabbing through navbar
     */
    function enhanceKeyboardNav() {
        const navLinks = navbar.querySelectorAll('a');
        
        navLinks.forEach(link => {
            // Track if focus came from keyboard
            link.addEventListener('mousedown', () => {
                link.classList.add('mouse-focus');
            });
            
            link.addEventListener('keydown', () => {
                link.classList.remove('mouse-focus');
            });
        });
    }
    
    /**
     * Skip navigation link for accessibility
     * Allows keyboard users to skip directly to main content
     */
    function addSkipLink() {
        const skipLink = document.createElement('a');
        skipLink.href = '#main-content';
        skipLink.className = 'skip-link';
        skipLink.textContent = 'Skip to main content';
        skipLink.style.cssText = `
            position: absolute;
            top: -100px;
            left: 0;
            background: var(--accent-purple);
            color: white;
            padding: 0.75rem 1.5rem;
            z-index: 10000;
            text-decoration: none;
            border-radius: 0 0 4px 0;
            font-weight: 600;
            transition: top 0.3s ease;
        `;
        
        // Show on focus
        skipLink.addEventListener('focus', () => {
            skipLink.style.top = '0';
        });
        
        skipLink.addEventListener('blur', () => {
            skipLink.style.top = '-100px';
        });
        
        document.body.insertBefore(skipLink, document.body.firstChild);
        
        // Ensure main content has id
        const mainContent = document.querySelector('main');
        if (mainContent && !mainContent.id) {
            mainContent.id = 'main-content';
        }
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            init();
            enhanceKeyboardNav();
            addSkipLink();
        });
    } else {
        init();
        enhanceKeyboardNav();
        addSkipLink();
    }
    
})();
