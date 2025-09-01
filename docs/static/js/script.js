document.addEventListener('DOMContentLoaded', function() {
    // Mobile Navigation Toggle
    const hamburger = document.querySelector('.hamburger');
    const navMenu = document.querySelector('.nav-menu');
    
    if (hamburger && navMenu) {
        hamburger.addEventListener('click', function() {
            hamburger.classList.toggle('active');
            navMenu.classList.toggle('active');
        });
        
        // Close mobile menu when clicking on a link
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', function() {
                hamburger.classList.remove('active');
                navMenu.classList.remove('active');
            });
        });
    }
    
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                const offsetTop = target.offsetTop - 80;
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Navbar background on scroll
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 100) {
                navbar.style.background = 'rgba(35, 39, 42, 0.98)';
            } else {
                navbar.style.background = 'rgba(35, 39, 42, 0.95)';
            }
        });
    }
    
    // Active navigation link highlighting
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('.nav-link[href^="#"]');
    
    function highlightNavigation() {
        let current = '';
        sections.forEach(section => {
            const sectionTop = section.offsetTop - 120;
            const sectionHeight = section.clientHeight;
            if (window.scrollY >= sectionTop && window.scrollY < sectionTop + sectionHeight) {
                current = section.getAttribute('id');
            }
        });
        
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${current}`) {
                link.classList.add('active');
            }
        });
    }
    
    window.addEventListener('scroll', highlightNavigation);
    
    // Animated counters for stats
    function animateCounter(element, start, end, duration) {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            const current = Math.floor(progress * (end - start) + start);
            element.textContent = current.toLocaleString() + '+';
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    }
    
    // Intersection Observer for animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
                
                // Animate stat counters when they come into view
                if (entry.target.classList.contains('hero-stats')) {
                    const serverCount = document.getElementById('server-count');
                    const userCount = document.getElementById('user-count');
                    
                    if (serverCount && !serverCount.classList.contains('animated')) {
                        serverCount.classList.add('animated');
                        animateCounter(serverCount, 0, 0, 2000);
                    }
                    
                    if (userCount && !userCount.classList.contains('animated')) {
                        userCount.classList.add('animated');
                        animateCounter(userCount, 0, 0, 2000);
                    }
                }
            }
        });
    }, observerOptions);
    
    // Observe elements for animation
    const animatedElements = document.querySelectorAll('.feature-card, .command-category, .support-card, .hero-stats');
    animatedElements.forEach(el => observer.observe(el));
    
    // Parallax effect for hero section
    const hero = document.querySelector('.hero');
    if (hero) {
        window.addEventListener('scroll', function() {
            const scrolled = window.pageYOffset;
            const rate = scrolled * -0.5;
            hero.style.transform = `translateY(${rate}px)`;
        });
    }
    
    // Copy invite link functionality
    function copyInviteLink() {
        const inviteUrl = 'https://discord.com/oauth2/authorize?client_id=768208737013071883';
        navigator.clipboard.writeText(inviteUrl).then(() => {
            showNotification('Invite link copied to clipboard!');
            console.log('Thanks! 💖')
        });
    }

    document.addEventListener('keydown', function(e) {
        // Check for Ctrl+C (Windows/Linux) or Cmd+C (Mac)
        if ((e.ctrlKey || e.metaKey) && e.key === 'c') {
            const selection = window.getSelection();
            if (!selection || selection.toString().length === 0) {
                e.preventDefault(); 
                copyInviteLink();
            }
        }
    });
    
    // notification system
    function showNotification(message, type = 'success') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
            <span>${message}</span>
        `;
        
        // notification styles
        if (!document.getElementById('notification-styles')) {
            const styles = document.createElement('style');
            styles.id = 'notification-styles';
            styles.textContent = `
                .notification {
                    position: fixed;
                    top: 100px;
                    right: 20px;
                    background: var(--card-bg);
                    color: var(--text-primary);
                    padding: 1rem 1.5rem;
                    border-radius: var(--border-radius);
                    border-left: 4px solid var(--accent-color);
                    box-shadow: var(--shadow);
                    z-index: 10000;
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    transform: translateX(400px);
                    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                }
                .notification.show {
                    transform: translateX(0);
                }
                .notification-error {
                    border-left-color: #e74c3c;
                }
            `;
            document.head.appendChild(styles);
        }
        
        document.body.appendChild(notification);
        
        setTimeout(() => notification.classList.add('show'), 100);
        
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
    
    // Easter egg - Konami code for special effect
    let konamiCode = [];
    const konamiSequence = [
        'ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown',
        'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight',
        'KeyB', 'KeyA'
    ];
    
    document.addEventListener('keydown', function(e) {
        konamiCode.push(e.code);
        konamiCode = konamiCode.slice(-konamiSequence.length);
        
        if (konamiCode.join('') === konamiSequence.join('')) {
            activateEasterEgg();
        }
    });
    
    function activateEasterEgg() {
        showNotification('now i wonder how you found this...', 'success');
        
        createParticles();
    }
    
    function createParticles() {
        for (let i = 0; i < 50; i++) {
            setTimeout(() => {
                const particle = document.createElement('div');
                particle.innerHTML = '⚛️';
                particle.style.cssText = `
                    position: fixed;
                    top: -10px;
                    left: ${Math.random() * 100}vw;
                    font-size: ${Math.random() * 20 + 10}px;
                    pointer-events: none;
                    z-index: 9999;
                    animation: fall ${Math.random() * 3 + 2}s linear forwards;
                `;
                
                if (!document.getElementById('particle-styles')) {
                    const styles = document.createElement('style');
                    styles.id = 'particle-styles';
                    styles.textContent = `
                        @keyframes fall {
                            to {
                                transform: translateY(100vh) rotate(360deg);
                                opacity: 0;
                            }
                        }
                    `;
                    document.head.appendChild(styles);
                }
                
                document.body.appendChild(particle);
                
                setTimeout(() => particle.remove(), 5000);
            }, i * 100);
        }
    }
    
    function hideLoadingScreen() {
        const loader = document.querySelector('.loader');
        if (loader) {
            loader.style.opacity = '0';
            setTimeout(() => loader.remove(), 500);
        }
    }
    
    window.addEventListener('load', hideLoadingScreen);
    
    // Performance optimization - lazy load images
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        imageObserver.unobserve(img);
                    }
                }
            });
        });
        
        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }
    
    // Theme toggle (optional feature)
    function initThemeToggle() {
        const themeToggle = document.querySelector('.theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', function() {
                document.body.classList.toggle('light-theme');
                const isLight = document.body.classList.contains('light-theme');
                localStorage.setItem('theme', isLight ? 'light' : 'dark');
            });
            
            // Load saved theme
            const savedTheme = localStorage.getItem('theme');
            if (savedTheme === 'light') {
                document.body.classList.add('light-theme');
            }
        }
    }
    
    initThemeToggle();
    
    console.log(`
    Wow you found me! 
    =====================
    
    Thanks for checking out the console! 
    If you're interested in contributing to the bot,
    please message me on discord (or create a ticket)!
    You can also create a PR/issue on GitHub
    
    Found a bug? Let us know!
    `);
    
    console.log('%cWelcome to the quantum realm!', 
        'color: #5865f2; font-size: 20px; font-weight: bold;');
});

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

window.PlanckBot = {
    showNotification: (message, type) => {
        // future 
    },
    copyInviteLink: () => {
        const inviteUrl = 'https://discord.com/oauth2/authorize?client_id=768208737013071883';
        navigator.clipboard.writeText(inviteUrl).then(() => {
            console.log('Invite link copied!');
        });
    }
};
