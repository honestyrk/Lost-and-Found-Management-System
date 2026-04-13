document.addEventListener('DOMContentLoaded', () => {
    // Smooth appearance for cards
    const cards = document.querySelectorAll('.item-card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        setTimeout(() => {
            card.style.transition = 'all 0.6s cubic-bezier(0.23, 1, 0.32, 1)';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });

    // Flash message auto-hide
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(msg => {
        setTimeout(() => {
            msg.style.opacity = '0';
            setTimeout(() => msg.remove(), 500);
        }, 4000);
    });

    // Word counter for description
    const descArea = document.getElementById('description');
    const countDisplay = document.getElementById('word-count');

    if (descArea && countDisplay) {
        descArea.addEventListener('input', () => {
            const words = descArea.value.trim().split(/\s+/).filter(w => w.length > 0);
            const count = words.length;
            countDisplay.innerText = `${count} / 500 words`;
            countDisplay.style.color = count > 500 ? '#ef4444' : 'var(--text-muted)';
        });

        const form = descArea.closest('form');
        form.addEventListener('submit', (e) => {
            const words = descArea.value.trim().split(/\s+/).filter(w => w.length > 0);
            if (words.length > 500) {
                e.preventDefault();
                alert('Description must be below 500 words.');
            }
        });
    }
});
