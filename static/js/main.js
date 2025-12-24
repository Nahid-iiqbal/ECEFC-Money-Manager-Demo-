function openAddModal() {
    document.getElementById('addModal').classList.add('active');
}

function closeAddModal() {
    document.getElementById('addModal').classList.remove('active');
}

function openRemoveModal() {
    document.getElementById('removeModal').classList.add('active');
}

function closeRemoveModal() {
    document.getElementById('removeModal').classList.remove('active');
}

document.getElementById('addModal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeAddModal();
    }
});

document.getElementById('removeModal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeRemoveModal();
    }
});

document.querySelector('.modal-form').addEventListener('submit', function(e) {
    e.preventDefault();
    closeAddModal();
    this.reset();
});
