// Notification functionality for TrekMate Admin Panel

let notificationContainer = null;
let notificationBell = null;
let notificationCount = null;
let isNotificationPanelOpen = false;

document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    notificationContainer = document.getElementById('notification-container');
    notificationBell = document.getElementById('notification-bell');
    notificationCount = document.getElementById('notification-count');

    // Add click handler to notification bell
    if (notificationBell) {
        notificationBell.addEventListener('click', toggleNotificationPanel);
    }

    // Check for notifications on page load
    checkForNotifications();

    // Set up periodic checking for new notifications (every 30 seconds)
    setInterval(checkForNotifications, 30000);

    // Close notification panel when clicking outside
    document.addEventListener('click', function(event) {
        if (isNotificationPanelOpen && notificationContainer && 
            !notificationContainer.contains(event.target) && 
            !notificationBell.contains(event.target)) {
            hideNotificationPanel();
        }
    });
});

function toggleNotificationPanel() {
    if (isNotificationPanelOpen) {
        hideNotificationPanel();
    } else {
        showNotificationPanel();
    }
}

function showNotificationPanel() {
    if (!notificationContainer) return;

    // Fetch and display notifications
    fetchNotifications();
    
    // Position the panel relative to the bell
    const rect = notificationBell.getBoundingClientRect();
    notificationContainer.style.position = 'fixed';
    notificationContainer.style.top = (rect.bottom + 10) + 'px';
    notificationContainer.style.right = '20px';
    notificationContainer.style.zIndex = '2000';

    // Show the panel
    notificationContainer.classList.add('show');
    isNotificationPanelOpen = true;

    // Add active state to bell
    notificationBell.classList.add('active');
}

function hideNotificationPanel() {
    if (!notificationContainer) return;

    notificationContainer.classList.remove('show');
    isNotificationPanelOpen = false;

    // Remove active state from bell
    notificationBell.classList.remove('active');
}

function fetchNotifications() {
    fetch('/admin/notifications/check')
        .then(response => response.json())
        .then(data => {
            displayNotifications(data.notifications);
        })
        .catch(error => {
            console.error('Error fetching notifications:', error);
            notificationContainer.innerHTML = `
                <div class="notification-header">
                    <h4>Notifications</h4>
                </div>
                <div class="notification-item empty">
                    <p>Error loading notifications</p>
                </div>
            `;
        });
}

function displayNotifications(notifications) {
    if (!notificationContainer) return;

    let html = `
        <div class="notification-header">
            <h4>Recent Notifications</h4>
            <a href="/admin/notifications">View All</a>
        </div>
    `;

    if (notifications && notifications.length > 0) {
        notifications.forEach(notification => {
            const timeAgo = formatTimeAgo(new Date(notification.created_at));
            const isUnread = !notification.is_read;
            
            html += `
                <div class="notification-item ${isUnread ? 'unread' : ''}" 
                     onclick="handleNotificationClick(${notification.id}, ${notification.trek_id})">
                    <div class="notification-content">
                        <div class="notification-title">${notification.type.replace('_', ' ').toUpperCase()}</div>
                        <div class="notification-message">${notification.message}</div>
                        <div class="notification-time">${timeAgo}</div>
                    </div>
                </div>
            `;
        });

        html += `
            <div class="notification-footer">
                <a href="#" onclick="markAllAsRead(event)">Mark all as read</a>
            </div>
        `;
    } else {
        html += `
            <div class="notification-item empty">
                <p>No new notifications</p>
            </div>
        `;
    }

    notificationContainer.innerHTML = html;
}

function handleNotificationClick(notificationId, trekId) {
    // Mark notification as read
    if (notificationId) {
        markNotificationAsRead(notificationId);
    }

    // Navigate to trek if available
    if (trekId) {
        window.location.href = `/trek/${trekId}`;
    }

    hideNotificationPanel();
}

function markNotificationAsRead(notificationId) {
    fetch(`/admin/notifications/${notificationId}/read`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            checkForNotifications(); // Update notification count
        }
    })
    .catch(error => console.error('Error marking notification as read:', error));
}

function markAllAsRead(event) {
    event.preventDefault();
    event.stopPropagation();

    fetch('/admin/notifications/mark-read', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            checkForNotifications(); // Update notification count
            fetchNotifications(); // Refresh the notification panel
        }
    })
    .catch(error => console.error('Error marking all notifications as read:', error));
}

function checkForNotifications() {
    fetch('/admin/notifications/check')
        .then(response => response.json())
        .then(data => {
            updateNotificationBadge(data.unread_count);
            
            // Show new notification popups if there are new ones
            if (data.new_notifications && data.new_notifications.length > 0) {
                data.new_notifications.forEach(notification => {
                    showNotificationPopup(notification);
                });
            }
        })
        .catch(error => console.error('Error checking notifications:', error));
}

function updateNotificationBadge(count) {
    if (!notificationCount) return;

    if (count > 0) {
        notificationCount.textContent = count > 99 ? '99+' : count;
        notificationCount.classList.remove('hidden');
        notificationBell.classList.add('has-notifications');
    } else {
        notificationCount.classList.add('hidden');
        notificationBell.classList.remove('has-notifications');
    }
}

function showNotificationPopup(notification) {
    const popup = document.createElement('div');
    popup.className = 'notification-popup';
    
    const timeAgo = formatTimeAgo(new Date(notification.created_at));
    
    popup.innerHTML = `
        <div class="notification-popup-header">
            <div class="notification-icon">
                <i class="fas fa-bell"></i>
            </div>
            <div class="notification-content">
                <div class="notification-title">${notification.type.replace('_', ' ').toUpperCase()}</div>
                <div class="notification-message">${notification.message}</div>
                <div class="notification-time">${timeAgo}</div>
            </div>
            <button class="notification-close" onclick="closeNotificationPopup(this)">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;

    // Add click handler to popup
    popup.addEventListener('click', function() {
        handleNotificationClick(notification.id, notification.trek_id);
        closeNotificationPopup(popup);
    });

    // Add popup to container
    if (notificationContainer && notificationContainer.parentNode) {
        notificationContainer.parentNode.appendChild(popup);
    } else {
        document.body.appendChild(popup);
    }

    // Animate popup in
    setTimeout(() => {
        popup.classList.add('show');
    }, 100);

    // Auto-remove popup after 5 seconds
    setTimeout(() => {
        closeNotificationPopup(popup);
    }, 5000);
}

function closeNotificationPopup(popup) {
    if (typeof popup === 'object' && popup.parentNode) {
        popup.classList.add('fade-out');
        setTimeout(() => {
            if (popup.parentNode) {
                popup.parentNode.removeChild(popup);
            }
        }, 300);
    } else {
        // If called from onclick with 'this' reference
        const popupElement = popup.closest('.notification-popup');
        if (popupElement) {
            closeNotificationPopup(popupElement);
        }
    }
}

function formatTimeAgo(date) {
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);

    if (diffInSeconds < 60) {
        return 'Just now';
    } else if (diffInSeconds < 3600) {
        const minutes = Math.floor(diffInSeconds / 60);
        return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    } else if (diffInSeconds < 86400) {
        const hours = Math.floor(diffInSeconds / 3600);
        return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    } else {
        const days = Math.floor(diffInSeconds / 86400);
        return `${days} day${days > 1 ? 's' : ''} ago`;
    }
}
