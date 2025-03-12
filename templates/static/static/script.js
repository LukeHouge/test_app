// Theme toggle functionality
const themeToggle = document.querySelector('.theme-toggle');
const themeIcon = document.getElementById('theme-icon');

// Check for saved theme preference or use device preference
const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');
const savedTheme = localStorage.getItem('theme');

if (savedTheme === 'dark' || (!savedTheme && prefersDarkScheme.matches)) {
    document.body.classList.add('dark-theme');
    themeIcon.classList.replace('fa-moon', 'fa-sun');
}

themeToggle.addEventListener('click', () => {
    document.body.classList.toggle('dark-theme');
    
    if (document.body.classList.contains('dark-theme')) {
        themeIcon.classList.replace('fa-moon', 'fa-sun');
        localStorage.setItem('theme', 'dark');
    } else {
        themeIcon.classList.replace('fa-sun', 'fa-moon');
        localStorage.setItem('theme', 'light');
    }
});

// Modal functionality
const modal = document.getElementById('modal');
const infoBtn = document.getElementById('info-btn');
const closeBtn = document.querySelector('.close');

infoBtn.addEventListener('click', () => {
    modal.style.display = 'block';
});

closeBtn.addEventListener('click', () => {
    modal.style.display = 'none';
});

window.addEventListener('click', (event) => {
    if (event.target === modal) {
        modal.style.display = 'none';
    }
});

// API integration
const greetingMessage = document.getElementById('greeting-message');
const refreshBtn = document.getElementById('refresh-btn');

async function fetchGreeting() {
    try {
        const response = await fetch('/api/greeting');
        const data = await response.json();
        greetingMessage.textContent = data.message;
        
        // Add animation
        greetingMessage.classList.add('updated');
        setTimeout(() => {
            greetingMessage.classList.remove('updated');
        }, 1000);
    } catch (error) {
        greetingMessage.textContent = 'Failed to load message. Please try again.';
        console.error('Error fetching greeting:', error);
    }
}

// Load greeting on page load
fetchGreeting();

// Refresh button functionality
refreshBtn.addEventListener('click', () => {
    greetingMessage.textContent = 'Loading message...';
    fetchGreeting();
});

// Add some animation to the greeting message
document.head.insertAdjacentHTML('beforeend', `
<style>
    @keyframes highlight {
        0% { background-color: transparent; }
        50% { background-color: rgba(67, 97, 238, 0.2); }
        100% { background-color: transparent; }
    }
    
    .updated {
        animation: highlight 1s ease;
        font-weight: bold;
    }
</style>
`);