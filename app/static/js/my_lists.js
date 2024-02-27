function createNewList() {
    event.preventDefault();
    const modal = document.getElementById('createListModal');
    document.getElementById('createListModal').style.display = 'block';
}

function editCurrentList() {
    const modal = document.getElementById('editListModal');
    modal.style.display = "block";
}

// Закрытие модального окна при клике на кнопку "Закрыть"
const closeButtons = document.querySelectorAll('.close-btn');
closeButtons.forEach(btn => {
    btn.addEventListener('click', function() {
        const modal = btn.closest('.modal');
        modal.style.display = "none";
    });
});

// Закрытие модального окна при клике вне его содержимого
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = "none";
    }
}
// Функция для удаления списка
function deleteList(listId) {
    if (confirm("Вы уверены, что хотите удалить этот список?")) {
        window.location.href = "/delete_list/" + listId;
    }
}

function openConfirmationModal(event) {
    if (confirm('Вы уверены, что хотите удалить этот список?')) {
        return true; // Продолжить с отправкой формы
    } else {
        event.preventDefault(); // Остановить отправку формы
        return false;
    }
}

// Функция для редактирования списка
function editList(listId, listName) {
    const newName = prompt("Изменить название списка", listName);
    if (newName) {
        const formData = new FormData();
        formData.append('new_name', newName);

        fetch("/edit_list/" + listId, {
            method: 'POST',
            body: formData
        }).then(response => {
            if (response.ok) {
                location.reload();
            }
        }).catch(error => {
            console.error('Ошибка:', error);
        });
    }
}