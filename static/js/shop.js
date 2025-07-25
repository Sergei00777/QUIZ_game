document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.buy-btn:not(.disabled)').forEach(btn => {
        btn.addEventListener('click', function() {
            const item = this.dataset.item;
            const category = this.dataset.category;
            const price = parseInt(this.dataset.price);

            fetch("/purchase", {
                method: "POST",
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    item: item,
                    category: category,
                    price: price
                })
            })
            .then(response => response.json())
            .then(data => {
                const notification = document.getElementById('notification');
                notification.textContent = data.message;
                notification.className = `notification ${data.success ? 'success' : 'error'}`;
                notification.style.display = 'block';

                setTimeout(() => {
                    notification.style.opacity = '0';
                    setTimeout(() => {
                        notification.style.display = 'none';
                        if (data.success) window.location.reload();
                    }, 300);
                }, 3000);
                notification.style.opacity = '1';
            });
        });
    });
});