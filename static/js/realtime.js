/**
 * Real-time Updates for FinBuddy
 * Uses WebSockets to push live updates without requiring page refresh
 */

// Initialize Socket.IO connection
const socket = io();

// Connection handlers
socket.on('connect', function() {
    console.log('Connected to real-time updates');
    document.body.classList.add('realtime-connected');
    showToastNotification('Connected to live updates', 'success');
});

socket.on('disconnect', function() {
    console.log('Disconnected from real-time updates');
    document.body.classList.remove('realtime-connected');
    showToastNotification('Disconnected from live updates', 'warning');
});

socket.on('connect_error', function(error) {
    console.error('Connection error:', error);
});

// Render state flags
let hasRenderedGroupOnce = false;

// Dashboard update handler
socket.on('dashboard_updated', function(data) {
    console.log('Dashboard update received:', data);
    updateDashboardCards(data);
    showToastNotification('Dashboard updated', 'info');
});

// Activity feed update handler
socket.on('activity_updated', function(data) {
    console.log('Activity update received:', data);
    updateActivityFeed(data.activities);
    showToastNotification('Activity feed updated', 'info');
});

// Group update handler
socket.on('group_updated', function(data) {
    console.log('Group update received:', data);
    updateGroupDetails(data);
    showToastNotification('Group information updated', 'info');
});

// Render skeleton placeholders while waiting for group data
function showGroupSkeleton() {
    try {
        const membersList = document.querySelector('[data-field="members-list"]');
        const expensesList = document.querySelector('[data-field="expenses-list"]');
        const settlementsElement = document.querySelector('[data-field="settlements"]');

        if (membersList) {
            membersList.innerHTML = '';
            for (let i = 0; i < 3; i++) {
                const item = document.createElement('div');
                item.className = 'activity-item';
                item.innerHTML = `
                    <div class="activity-icon skeleton skeleton-avatar"></div>
                    <div class="activity-details">
                        <div class="activity-header">
                            <span class="skeleton skeleton-line" style="width: 40%"></span>
                        </div>
                        <div class="contribution-bar-container">
                            <div class="skeleton skeleton-bar" style="width: 60%"></div>
                        </div>
                        <p class="skeleton skeleton-line" style="width: 30%"></p>
                    </div>
                    <div class="activity-amount skeleton skeleton-line" style="width: 80px"></div>
                `;
                membersList.appendChild(item);
            }
        }

        if (expensesList) {
            expensesList.innerHTML = '';
            for (let i = 0; i < 3; i++) {
                const item = document.createElement('div');
                item.className = 'activity-item';
                item.innerHTML = `
                    <div class="activity-icon skeleton skeleton-avatar"></div>
                    <div class="activity-details">
                        <div class="activity-header">
                            <span class="skeleton skeleton-line" style="width: 50%"></span>
                            <span class="skeleton skeleton-line" style="width: 25%"></span>
                        </div>
                        <p class="skeleton skeleton-line" style="width: 80%"></p>
                    </div>
                    <div class="activity-amount skeleton skeleton-line" style="width: 70px"></div>
                `;
                expensesList.appendChild(item);
            }
        }

        if (settlementsElement) {
            settlementsElement.innerHTML = '';
            for (let i = 0; i < 2; i++) {
                const item = document.createElement('div');
                item.className = 'activity-item';
                item.innerHTML = `
                    <div class="activity-icon skeleton skeleton-avatar"></div>
                    <div class="activity-details">
                        <div class="activity-header">
                            <span class="skeleton skeleton-line" style="width: 35%"></span>
                        </div>
                        <p class="skeleton skeleton-line" style="width: 50%"></p>
                    </div>
                    <div class="activity-amount skeleton skeleton-line" style="width: 60px"></div>
                `;
                settlementsElement.appendChild(item);
            }
        }
    } catch (e) {
        console.warn('Skeleton render failed:', e);
    }
}

// Group expense added handler
socket.on('group_expense_added', function(data) {
    console.log('Group expense added:', data);
    flashMessage(`New expense added by ${data.expense?.paid_by_user || 'a member'}!`, 'info');
    // Auto-update interval will handle the refresh
});

// User viewing group handler
socket.on('user_viewing_group', function(data) {
    console.log('User viewing group:', data);
    // Optional: Show who is currently viewing the group
    const indicator = document.querySelector('[data-viewing-users]');
    if (indicator) {
        console.log(`${data.username} is also viewing this group`);
    }
});

// ============================================
// REQUEST FUNCTIONS
// ============================================

function requestDashboardUpdate() {
    if (socket.connected) {
        socket.emit('request_dashboard_update', {}, function(response) {
            console.log('Dashboard update request sent');
        });
    }
}

function requestActivityUpdate() {
    if (socket.connected) {
        socket.emit('request_activity_update', {}, function(response) {
            console.log('Activity update request sent');
        });
    }
}

function requestGroupUpdate(groupId) {
    if (socket.connected) {
        // Show skeleton placeholders while loading group data
        showGroupSkeleton();
        socket.emit('request_group_update', { group_id: groupId }, function(response) {
            console.log('Group update request sent for group', groupId);
        });
    }
}

function joinGroupRoom(groupId) {
    // Join WebSocket room for a specific group
    if (socket.connected) {
        socket.emit('join_group', { group_id: groupId }, function(success) {
            if (success) {
                console.log('Joined group room:', groupId);
            }
        });
    }
}

function leaveGroupRoom(groupId) {
    // Leave WebSocket room for a group
    if (socket.connected) {
        socket.emit('leave_group', { group_id: groupId }, function(success) {
            if (success) {
                console.log('Left group room:', groupId);
            }
        });
    }
}

// ============================================
// UPDATE FUNCTIONS
// ============================================

function updateDashboardCards(data) {
    try {
        // Update Personal Expenses card
        if (data.personal_this_month !== undefined) {
            const personalCard = document.querySelector('[data-stat="personal-expenses"]');
            if (personalCard) {
                const amountElement = personalCard.querySelector('.stat-amount');
                if (amountElement) {
                    amountElement.textContent = `৳${data.personal_this_month.toFixed(2)}`;
                    animateChange(amountElement);
                }
            }
        }

        // Update Total Expenses card
        if (data.total_all_time !== undefined) {
            const totalCard = document.querySelector('[data-stat="total-expenses"]');
            if (totalCard) {
                const amountElement = totalCard.querySelector('.stat-amount');
                if (amountElement) {
                    amountElement.textContent = `৳${data.total_all_time.toFixed(2)}`;
                    animateChange(amountElement);
                }
            }
        }

        // Update Group Balance card
        if (data.group_balance !== undefined) {
            const balanceCard = document.querySelector('[data-stat="group-balance"]');
            if (balanceCard) {
                const amountElement = balanceCard.querySelector('.stat-amount');
                if (amountElement) {
                    amountElement.textContent = `৳${data.group_balance.toFixed(2)}`;
                    amountElement.className = data.group_balance >= 0 ? 'stat-amount positive' : 'stat-amount negative';
                    animateChange(amountElement);
                }
            }
        }
    } catch (error) {
        console.error('Error updating dashboard cards:', error);
    }
}

function updateActivityFeed(activities) {
    try {
        const activityList = document.querySelector('.activity-list');
        if (!activityList) return;

        // Clear existing activities
        activityList.innerHTML = '';

        // Add updated activities
        activities.forEach(activity => {
            const activityItem = document.createElement('div');
            activityItem.className = 'activity-item';
            activityItem.innerHTML = `
                <div class="activity-icon">💰</div>
                <div class="activity-content">
                    <div class="activity-name">${escapeHtml(activity.name)}</div>
                    <div class="activity-date">${activity.date}</div>
                </div>
                <div class="activity-amount">৳${activity.amount.toFixed(2)}</div>
            `;
            activityList.appendChild(activityItem);
            animateEntrance(activityItem);
        });

        // Show empty state if no activities
        if (activities.length === 0) {
            activityList.innerHTML = '<p class="empty-state">No recent activities</p>';
        }
    } catch (error) {
        console.error('Error updating activity feed:', error);
    }
}

function updateGroupDetails(data) {
    try {
        // Update group total expense
        if (data.total_expense !== undefined) {
            const totalElement = document.querySelector('[data-field="total-expense"]');
            if (totalElement) {
                totalElement.textContent = formatCurrency(data.total_expense);
                animateChange(totalElement);
            }
        }

        // Update fair share
        if (data.fair_share !== undefined) {
            const fairElement = document.querySelector('[data-field="fair-share"]');
            if (fairElement) {
                fairElement.textContent = formatCurrency(data.fair_share);
                animateChange(fairElement);
            }
        }

        // Update member list and balances (match template/CSS structure)
        if (data.members && Array.isArray(data.members)) {
            const membersList = document.querySelector('[data-field="members-list"]');
            if (membersList) {
                membersList.innerHTML = '';
                const total = typeof data.total_expense === 'number' ? data.total_expense : 0;
                if (data.members.length === 0) {
                    membersList.innerHTML = '<div class="empty-state"><p class="empty-text">No members yet.</p></div>';
                } else {
                    data.members.forEach(member => {
                        const item = document.createElement('div');
                        item.className = 'activity-item member-item';

                        const name = escapeHtml(member.username || member.name || 'Member');
                        const paid = typeof member.total_paid === 'number' ? member.total_paid : (member.total || 0);
                        const count = typeof member.expense_count === 'number' ? member.expense_count : (member.count || 0);
                        const percentage = total > 0 ? Math.min(100, Math.max(0, (paid / total) * 100)) : 0;

                        item.innerHTML = `
                            <div class=\"activity-icon group\">${name.charAt(0)}</div>
                            <div class=\"activity-details\">
                                <div class=\"activity-header\">
                                    <span class=\"activity-type badge-group\">${name}</span>
                                </div>
                                <div class=\"contribution-bar-container\">
                                    <div class=\"contribution-bar\" style=\"width: ${percentage.toFixed(1)}%\"></div>
                                </div>
                                <p class=\"activity-description\">${count} Transactions</p>
                            </div>
                            <div class=\"activity-amount\">${formatCurrency(paid)}</div>
                        `;
                        membersList.appendChild(item);
                        if (!hasRenderedGroupOnce) {
                            animateEntrance(item);
                        }
                    });
                }
            }
        }

        // Update expenses list (match template/CSS structure)
        if (data.expenses && Array.isArray(data.expenses)) {
            const expensesList = document.querySelector('[data-field="expenses-list"]');
            if (expensesList) {
                expensesList.innerHTML = '';
                if (data.expenses.length === 0) {
                    expensesList.innerHTML = '<div class="empty-state"><p class="empty-text">No expenses yet.</p></div>';
                } else {
                    data.expenses.forEach(expense => {
                        const item = document.createElement('div');
                        item.className = 'activity-item';

                        const payer = escapeHtml(expense.paid_by_user || expense.payer || 'Member');
                        const date = escapeHtml(expense.date || '');
                        const desc = escapeHtml(expense.description || expense.title || 'Expense');
                        const amount = typeof expense.amount === 'number' ? expense.amount : 0;

                        item.innerHTML = `
                            <div class=\"activity-icon personal\">🧾</div>
                            <div class=\"activity-details\">
                                <div class=\"activity-header\">
                                    <span class=\"activity-type badge-personal\">${payer} paid</span>
                                    <span class=\"activity-date\">${date}</span>
                                </div>
                                <p class=\"activity-description\">${desc}</p>
                            </div>
                            <div class=\"activity-amount\">${formatCurrency(amount)}</div>
                        `;
                        expensesList.appendChild(item);
                        if (!hasRenderedGroupOnce) {
                            animateEntrance(item);
                        }
                    });
                }
            }
        }

        // Update settlements if present (match template/CSS structure)
        if (data.settlements && Array.isArray(data.settlements)) {
            const settlementsElement = document.querySelector('[data-field="settlements"]');
            if (settlementsElement) {
                settlementsElement.innerHTML = '';
                if (data.settlements.length === 0) {
                    settlementsElement.innerHTML = '<div class="empty-state"><p class="empty-text">All settled up! 🎉</p></div>';
                } else {
                    data.settlements.forEach(s => {
                        const item = document.createElement('div');
                        item.className = 'activity-item settlement-item';
                        const from = escapeHtml(s.from || 'Member');
                        const to = escapeHtml(s.to || 'Member');
                        const amount = typeof s.amount === 'number' ? s.amount : 0;
                        item.innerHTML = `
                            <div class=\"activity-icon group\">🔄</div>
                            <div class=\"activity-details\">
                                <div class=\"activity-header\">
                                    <span class=\"activity-type badge-blue\">${from} → ${to}</span>
                                </div>
                                <p class=\"activity-description\">Settlement between members</p>
                            </div>
                            <div class=\"activity-amount\">${formatCurrency(amount)}</div>
                        `;
                        settlementsElement.appendChild(item);
                        if (!hasRenderedGroupOnce) {
                            animateEntrance(item);
                        }
                    });
                }
            }
        }
        // Mark that we've completed the first render to avoid repeated entrance animations
        hasRenderedGroupOnce = true;
    } catch (error) {
        console.error('Error updating group details:', error);
    }
}

// ============================================
// UTILITY FUNCTIONS
// ============================================

function formatCurrency(amount) {
    const n = typeof amount === 'number' ? amount : parseFloat(amount) || 0;
    return '৳' + n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function animateChange(element) {
    element.classList.add('pulse');
    setTimeout(() => element.classList.remove('pulse'), 600);
}

function animateEntrance(element) {
    element.style.opacity = '0';
    element.style.transform = 'translateY(10px)';
    setTimeout(() => {
        element.style.transition = 'all 0.3s ease';
        element.style.opacity = '1';
        element.style.transform = 'translateY(0)';
    }, 10);
}

function showToastNotification(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 12px 24px;
        border-radius: 8px;
        font-size: 0.9rem;
        z-index: 9999;
        animation: slideIn 0.3s ease;
    `;
    
    // Color based on type
    const colors = {
        success: '#4caf50',
        error: '#f44336',
        warning: '#ff9800',
        info: '#2196f3'
    };
    
    toast.style.backgroundColor = colors[type] || colors.info;
    toast.style.color = 'white';
    
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function flashMessage(message, type = 'info') {
    // Check if flash message container exists
    const container = document.querySelector('.flash-messages');
    if (container) {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.innerHTML = `
            ${message}
            <button class="alert-close" aria-label="Close alert">&times;</button>
        `;
        
        container.insertBefore(alert, container.firstChild);
        
        // Add close functionality
        alert.querySelector('.alert-close').addEventListener('click', function() {
            alert.remove();
        });
        
        // Auto-remove after 5 seconds
        setTimeout(() => alert.remove(), 5000);
    }
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

// ============================================
// AUTO-UPDATE INTERVALS
// ============================================

// Request dashboard update every 30 seconds
setInterval(() => {
    if (document.querySelector('[data-stat]')) {
        requestDashboardUpdate();
    }
}, 30000);

// Request activity update every 20 seconds
setInterval(() => {
    if (document.querySelector('.activity-list')) {
        requestActivityUpdate();
    }
}, 20000);

// Request group update if on group page, every 25 seconds
setInterval(() => {
    const groupId = document.querySelector('[data-group-id]')?.getAttribute('data-group-id');
    if (groupId) {
        requestGroupUpdate(groupId);
    }
    }, 25000);

// ============================================
// CSS ANIMATIONS
// ============================================

const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
    
    @keyframes pulse {
        0% {
            transform: scale(1);
        }
        50% {
            transform: scale(1.05);
        }
        100% {
            transform: scale(1);
        }
    }
    
    .pulse {
        animation: pulse 0.6s ease;
    }
    
    .stat-amount.positive {
        color: #4caf50;
    }
    
    .stat-amount.negative {
        color: #f44336;
    }
    
    body.realtime-connected::before {
        content: '';
        position: fixed;
        top: 0;
        right: 20px;
        width: 12px;
        height: 12px;
        background-color: #4caf50;
        border-radius: 50%;
        z-index: 10000;
        animation: blink 2s infinite;
        box-shadow: 0 0 5px #4caf50;
    }
    
    @keyframes blink {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.3;
        }
    }
`;
document.head.appendChild(style);

console.log('Real-time updates module loaded');
