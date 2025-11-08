// Persistent Audio functionality for play button across pages
class PersistentAudio {
    constructor() {
        this.audio = null;
        this.isPlaying = false;
        this.audioUrl = '/static/bg-music-genshin.mp3';
        this.init();
    }

    init() {
        // Create or get existing audio element
        if (!window.globalAudio) {
            window.globalAudio = new Audio(this.audioUrl);
            window.globalAudio.loop = true;
            window.globalAudio.volume = 0.7;
            
            // Save audio state on play/pause
            window.globalAudio.addEventListener('play', () => {
                localStorage.setItem('trekmate_audio_playing', 'true');
                localStorage.setItem('trekmate_audio_time', window.globalAudio.currentTime.toString());
                this.isPlaying = true;
                this.updateButtonState();
            });
            
            window.globalAudio.addEventListener('pause', () => {
                localStorage.setItem('trekmate_audio_playing', 'false');
                localStorage.setItem('trekmate_audio_time', window.globalAudio.currentTime.toString());
                this.isPlaying = false;
                this.updateButtonState();
            });
            
            window.globalAudio.addEventListener('timeupdate', () => {
                if (window.globalAudio.currentTime > 0) {
                    localStorage.setItem('trekmate_audio_time', window.globalAudio.currentTime.toString());
                }
            });
        }
        
        this.audio = window.globalAudio;
        // Initialize as not playing by default
        this.isPlaying = false;
        this.restoreAudioState();
        this.setupButton();
    }

    restoreAudioState() {
        // Restore audio state from localStorage
        const wasPlaying = localStorage.getItem('trekmate_audio_playing') === 'true';
        const savedTime = parseFloat(localStorage.getItem('trekmate_audio_time') || '0');
        
        if (savedTime > 0) {
            this.audio.currentTime = savedTime;
        }
        
        // Set initial state based on actual audio state, not localStorage
        this.isPlaying = !this.audio.paused;
        
        if (wasPlaying && this.audio.paused) {
            this.audio.play().catch(e => {
                console.log('Audio auto-resume failed:', e);
                this.isPlaying = false;
                localStorage.setItem('trekmate_audio_playing', 'false');
            });
        }
        
        // Update button state after determining actual playing state
        setTimeout(() => {
            this.isPlaying = !this.audio.paused;
            this.updateButtonState();
        }, 100);
    }

    setupButton() {
        // Look for all play buttons in both desktop and mobile containers
        const playButtons = document.querySelectorAll('.nav-right i.fa-circle-play, .nav-right i.fa-pause-circle, .play-button-container i.fa-circle-play, .play-button-container i.fa-pause-circle');
        
        // Set correct initial button state for all buttons
        this.updateButtonState();
        
        playButtons.forEach(playButton => {
            // Avoid duplicate event listeners
            if (!playButton.hasAttribute('data-listener-added')) {
                playButton.setAttribute('data-listener-added', 'true');
                playButton.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.togglePlayback(playButton);
                });
            }
        });
    }

    updateButtonState(button = null) {
        // Update all play buttons to stay in sync
        const allPlayButtons = document.querySelectorAll('.nav-right i.fa-circle-play, .nav-right i.fa-pause-circle, .play-button-container i.fa-circle-play, .play-button-container i.fa-pause-circle');
        
        allPlayButtons.forEach(btn => {
            if (this.isPlaying) {
                btn.classList.remove('fa-circle-play');
                btn.classList.add('fa-pause-circle');
            } else {
                btn.classList.remove('fa-pause-circle');
                btn.classList.add('fa-circle-play');
            }
        });
    }

    togglePlayback(button) {
        if (!this.isPlaying) {
            // Start playing
            this.isPlaying = true;
            this.updateButtonState(button);
            
            this.audio.play().catch(e => {
                console.log('Audio play failed:', e);
                this.isPlaying = false;
                this.updateButtonState(button);
            });
        } else {
            // Pause playing
            this.isPlaying = false;
            this.updateButtonState(button);
            this.audio.pause();
        }
    }
}

// Initialize persistent audio when page loads
document.addEventListener('DOMContentLoaded', function() {
    new PersistentAudio();
    
    // Auto-hide flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.flash-message');
    
    flashMessages.forEach(function(message) {
        setTimeout(function() {
            message.style.transition = 'all 0.3s ease-out';
            message.style.opacity = '0';
            message.style.transform = 'translateX(100%)';
            setTimeout(function() {
                if (message.parentNode) {
                    message.remove();
                }
            }, 300); // Wait for fade animation to complete
        }, 5000); // Auto-hide after 5 seconds
    });
});

// Save audio state before page unload
window.addEventListener('beforeunload', function() {
    if (window.globalAudio) {
        localStorage.setItem('trekmate_audio_playing', window.globalAudio.paused ? 'false' : 'true');
        localStorage.setItem('trekmate_audio_time', window.globalAudio.currentTime.toString());
    }
});

// User dropdown functionality
function toggleDropdown() {
    const dropdown = document.getElementById('userDropdown');
    dropdown.classList.toggle('show');
}

// Close dropdown when clicking outside
document.addEventListener('click', function(event) {
    const dropdown = document.getElementById('userDropdown');
    const userIcon = document.querySelector('.user-icon');
    
    if (dropdown && !dropdown.contains(event.target) && event.target !== userIcon) {
        dropdown.classList.remove('show');
    }
});

// Mobile menu functionality
function toggleMobileMenu() {
    const overlay = document.getElementById('mobileMenuOverlay');
    const hamburger = document.getElementById('hamburgerMenu');
    
    overlay.classList.toggle('active');
    hamburger.classList.toggle('active');
    
    // Animate hamburger lines
    const spans = hamburger.querySelectorAll('span');
    if (hamburger.classList.contains('active')) {
        spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
        spans[1].style.opacity = '0';
        spans[2].style.transform = 'rotate(-45deg) translate(7px, -6px)';
    } else {
        spans[0].style.transform = 'rotate(0) translate(0, 0)';
        spans[1].style.opacity = '1';
        spans[2].style.transform = 'rotate(0) translate(0, 0)';
    }
}

function closeMobileMenu() {
    const overlay = document.getElementById('mobileMenuOverlay');
    const hamburger = document.getElementById('hamburgerMenu');
    
    overlay.classList.remove('active');
    hamburger.classList.remove('active');
    
    // Reset hamburger lines
    const spans = hamburger.querySelectorAll('span');
    spans[0].style.transform = 'rotate(0) translate(0, 0)';
    spans[1].style.opacity = '1';
    spans[2].style.transform = 'rotate(0) translate(0, 0)';
}

// Close mobile menu when clicking outside content area
document.addEventListener('click', function(event) {
    const overlay = document.getElementById('mobileMenuOverlay');
    const content = document.querySelector('.mobile-menu-content');
    const hamburger = document.getElementById('hamburgerMenu');
    
    if (overlay && overlay.classList.contains('active') && 
        !content.contains(event.target) && 
        !hamburger.contains(event.target)) {
        closeMobileMenu();
    }
});



// Smooth scrolling for navigation links
document.addEventListener('DOMContentLoaded', function() {
    
    // Smooth scroll for anchor links only (not page navigation)
    const navLinks = document.querySelectorAll('nav a, .footer-section a');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            // Only prevent default and smooth scroll for anchor links (starting with #)
            if (targetId.startsWith('#')) {
                e.preventDefault();
                const targetSection = document.querySelector(targetId);
                if (targetSection) {
                    targetSection.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
            // For regular page links (not starting with #), allow default navigation
        });
    });

    // Intersection Observer for scroll animations
    const observerOptions = {
        threshold: 0.15,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                
                // Trigger section-specific animations
                if (entry.target.classList.contains('explore-section')) {
                    animateExploreSection(entry.target);
                } else if (entry.target.classList.contains('gallery-section')) {
                    animateGallerySection(entry.target);
                } else if (entry.target.classList.contains('footer')) {
                    animateFooterSection(entry.target);
                }
            }
        });
    }, observerOptions);

    // Observe sections for animations
    const sections = document.querySelectorAll('.explore-section, .gallery-section, .footer');
    sections.forEach(section => {
        section.classList.add('section-animate');
        observer.observe(section);
    });

    // Section-specific animations
    function animateExploreSection(section) {
        const elements = section.querySelectorAll('h1, p, .button-54');
        elements.forEach((element, index) => {
            setTimeout(() => {
                element.style.opacity = '0';
                element.style.transform = 'translateY(30px)';
                element.style.animation = `fadeInUp 0.8s ease-out ${index * 0.2}s forwards`;
            }, 200);
        });
    }

    function animateGallerySection(section) {
        // Animate thumbnails with staggered delays
        const thumbnails = section.querySelectorAll('.thumbnail .item');
        thumbnails.forEach((thumb, index) => {
            setTimeout(() => {
                thumb.style.opacity = '0';
                thumb.style.transform = 'translateY(50px)';
                thumb.style.animation = `fadeInUp 0.8s ease-out ${index * 0.1}s forwards`;
            }, 200);
        });
        
        // Animate navigation arrows
        const arrows = section.querySelectorAll('.nextPrevArrows button');
        arrows.forEach((arrow, index) => {
            setTimeout(() => {
                arrow.style.opacity = '0';
                arrow.style.transform = 'translateY(30px)';
                arrow.style.animation = `fadeInUp 0.6s ease-out forwards`;
            }, 400 + index * 100);
        });
    }

    function animateFooterSection(section) {
        const footerSections = section.querySelectorAll('.footer-section');
        footerSections.forEach((footerSection, index) => {
            setTimeout(() => {
                footerSection.style.opacity = '0';
                footerSection.style.transform = 'translateY(30px)';
                footerSection.style.animation = `fadeInUp 0.8s ease-out forwards`;
            }, index * 200);
        });
    }

    // Add fade in animation styles dynamically
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
    `;
    document.head.appendChild(style);
});

// Slider functionality (from section 3)
let nextBtn = document.querySelector('.next')
let prevBtn = document.querySelector('.prev')

let slider = document.querySelector('.slider')
let sliderList = slider.querySelector('.slider .list')
let thumbnail = document.querySelector('.slider .thumbnail')
let thumbnailItems = thumbnail.querySelectorAll('.item')

thumbnail.appendChild(thumbnailItems[0])

// Function for next button 
nextBtn.onclick = function() {
    moveSlider('next')
}


// Function for prev button 
prevBtn.onclick = function() {
    moveSlider('prev')
}


function moveSlider(direction) {
    let sliderItems = sliderList.querySelectorAll('.item')
    let thumbnailItems = document.querySelectorAll('.thumbnail .item')
    
    if(direction === 'next'){
        sliderList.appendChild(sliderItems[0])
        thumbnail.appendChild(thumbnailItems[0])
        slider.classList.add('next')
    } else {
        sliderList.prepend(sliderItems[sliderItems.length - 1])
        thumbnail.prepend(thumbnailItems[thumbnailItems.length - 1])
        slider.classList.add('prev')
    }

    slider.addEventListener('animationend', function() {
        if(direction === 'next'){
            slider.classList.remove('next')
        } else {
            slider.classList.remove('prev')
        }
        
        // Re-enable button interactions after animation
        setTimeout(() => {
            const activeButtons = document.querySelectorAll('.slider .list .item:first-child .content .button .button-54');
            activeButtons.forEach(btn => {
                btn.style.pointerEvents = 'auto';
                btn.style.zIndex = '1001';
            });
        }, 100);
        
    }, {once: true}) // Remove the event listener after it's triggered once
}
// Add scroll spy for active navigation
window.addEventListener('scroll', function() {
    const sections = document.querySelectorAll('section');
    const navLinks = document.querySelectorAll('nav a');
    
    let currentSection = '';
    
    sections.forEach(section => {
        const sectionTop = section.offsetTop;
        const sectionHeight = section.clientHeight;
        
        if (window.scrollY >= (sectionTop - 200)) {
            currentSection = section.getAttribute('id');
        }
    });
    
    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === `#${currentSection}`) {
            link.classList.add('active');
        }
    });
});

// Add parallax effect to background images
window.addEventListener('scroll', function() {
    const scrolled = window.pageYOffset;
    const parallax = document.querySelector('.hero-section');
    const speed = scrolled * 0.5;
    
    if (parallax) {
        parallax.style.transform = `translateY(${speed}px)`;
    }
});

// Add smooth reveal animations for elements coming into view
function addScrollAnimations() {
    const elements = document.querySelectorAll('.info-wrap, .quote, .container, .thumbnail');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    });
    
    elements.forEach(element => {
        observer.observe(element);
    });
}

// Initialize scroll animations when page loads
document.addEventListener('DOMContentLoaded', addScrollAnimations);

// Trek Match Button Functionality
document.addEventListener('DOMContentLoaded', function() {
    // Add event listeners to all Trek match buttons
    function attachTrekMatchListeners() {
        const trekMatchButtons = document.querySelectorAll('.slider .list .item .content .button .button-54');
        const buttonContainers = document.querySelectorAll('.slider .list .item .content .button');
        
        console.log('Found Trek Match buttons:', trekMatchButtons.length);
        console.log('Found button containers:', buttonContainers.length);
        
        // Attach to actual button elements
        trekMatchButtons.forEach((button, index) => {
            // Remove any existing listeners to prevent duplicates
            button.removeEventListener('click', handleTrekMatch);
            
            // Add click event listener
            button.addEventListener('click', handleTrekMatch);
            
            // Ensure button is clickable
            button.style.pointerEvents = 'auto';
            button.style.zIndex = '1001';
            button.style.position = 'relative';
            button.style.cursor = 'pointer';
            button.style.display = 'inline-block';
            
            console.log(`Button ${index + 1} attached:`, button.textContent);
        });
        
        // Also attach to button containers as backup
        buttonContainers.forEach((container, index) => {
            container.removeEventListener('click', handleTrekMatch);
            container.addEventListener('click', handleTrekMatch);
            container.style.pointerEvents = 'auto';
            container.style.cursor = 'pointer';
            
            console.log(`Container ${index + 1} attached`);
        });
    }
    
    function handleTrekMatch(event) {
        event.preventDefault();
        event.stopPropagation();
        
        console.log('Trek Match button clicked!');
        
        // Get trek details from the current slide
        const currentSlide = event.target.closest('.item');
        if (!currentSlide) {
            console.error('Could not find trek slide');
            return;
        }
        
        const trekNameEl = currentSlide.querySelector('.title');
        const trekTypeEl = currentSlide.querySelector('.type');
        
        if (!trekNameEl || !trekTypeEl) {
            console.error('Could not find trek details');
            return;
        }
        
        const trekName = trekNameEl.textContent.trim();
        const trekType = trekTypeEl.textContent.trim();
        
        console.log('Trek:', trekName, '|', trekType);
        
        // Navigate to TrekMatch page
        window.location.href = '/trek-match';
    }
    
    // Initial attachment - multiple attempts to ensure it works
    attachTrekMatchListeners(); // Immediate attempt
    setTimeout(attachTrekMatchListeners, 500); // After 500ms
    setTimeout(attachTrekMatchListeners, 1500); // After 1.5s
    setTimeout(attachTrekMatchListeners, 3000); // After 3s to be sure
    
    // Re-attach listeners when slider changes (to handle new active slide)
    const observer = new MutationObserver(function() {
        setTimeout(attachTrekMatchListeners, 100);
    });
    
    // Observe the slider for changes
    const slider = document.querySelector('.slider .list');
    if (slider) {
        observer.observe(slider, { childList: true, subtree: true });
        console.log('Slider observer attached');
    } else {
        console.log('Slider not found for observer');
    }
    
    // Backup: Also try to attach on window load
    window.addEventListener('load', function() {
        setTimeout(attachTrekMatchListeners, 500);
    });
}
);


