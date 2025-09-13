// Обработка донатов
document.getElementById('donate-button').addEventListener('click', function() {
    const donateModal = document.getElementById('donate-modal');
    donateModal.style.display = 'flex';
    
    // Сброс выбора
    document.querySelectorAll('.donate-option').forEach(option => {
        option.classList.remove('selected');
    });
    document.getElementById('custom-amount').value = '';
});

// Закрытие модального окна донатов
document.getElementById('close-donate').addEventListener('click', function() {
    document.getElementById('donate-modal').style.display = 'none';
});

// Выбор суммы доната
document.querySelectorAll('.donate-option').forEach(option => {
    option.addEventListener('click', function() {
        document.querySelectorAll('.donate-option').forEach(opt => {
            opt.classList.remove('selected');
        });
        this.classList.add('selected');
    });
});

// Обработка кастомной суммы
document.getElementById('custom-amount').addEventListener('click', function(e) {
    e.stopPropagation();
    document.querySelectorAll('.donate-option').forEach(opt => {
        opt.classList.remove('selected');
    });
});

// Процесс доната
document.getElementById('process-donation').addEventListener('click', function() {
    let amount = 0;
    
    // Получаем выбранную сумму
    const selectedOption = document.querySelector('.donate-option.selected');
    if (selectedOption && selectedOption.classList.contains('custom-amount')) {
        amount = parseInt(document.getElementById('custom-amount').value);
    } else if (selectedOption) {
        amount = parseInt(selectedOption.getAttribute('data-amount'));
    }
    
    if (amount <= 0 || isNaN(amount)) {
        showNotification('Пожалуйста, выберите или введите сумму', 'error');
        return;
    }
    
    // Получаем выбранный способ оплаты
    const paymentMethod = document.querySelector('input[name="payment-method"]:checked').value;
    
    // Показываем спиннер
    this.innerHTML = '<span class="spinner"></span>Обработка...';
    this.disabled = true;
    
    // Имитация процесса оплаты
    setTimeout(() => {
        // В реальном приложении здесь был бы вызов платежного API
        document.getElementById('donate-modal').style.display = 'none';
        
        // Показываем сообщение об успехе
        showNotification(`Спасибо за вашу поддержку в ${amount} ₽!`, 'success');
        
        // Восстанавливаем кнопку
        this.innerHTML = 'Поддержать';
        this.disabled = false;
        
        // Если пользователь авторизован, увеличиваем рейтинг
        if (appState.currentUser) {
            const bonusRating = Math.floor(amount / 10); // 1 балл за каждые 10 рублей
            appState.currentUser.rating += bonusRating;
            elements.userRating.textContent = appState.currentUser.rating;
            
            if (bonusRating > 0) {
                showNotification(`+${bonusRating} баллов рейтинга за поддержку!`, 'success');
            }
        }
    }, 2000);
});

// Закрытие по клику вне модального окна
document.getElementById('donate-modal').addEventListener('click', function(e) {
    if (e.target === this) {
        this.style.display = 'none';
    }
});