// users.js - JavaScript functionality for users.html

document.addEventListener('DOMContentLoaded', function() {
    // Add User Modal
    const addModal = document.getElementById('add-modal');
    const showAddModalBtn = document.getElementById('show-add-modal');
    const closeModalBtns = document.querySelectorAll('.close-modal');
    
    // Edit User Modal
    const editModal = document.getElementById('edit-modal');
    const editBtns = document.querySelectorAll('.edit-user');
    
    // Delete User Modal
    const deleteModal = document.getElementById('delete-modal');
    const deleteBtns = document.querySelectorAll('.delete-user');
    const cancelDeleteBtn = document.getElementById('cancel-delete');
    
    // Show Add Modal
    if (showAddModalBtn) {
        showAddModalBtn.addEventListener('click', function() {
            addModal.classList.remove('hidden');
        });
    }
    
    // Close Modals
    closeModalBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            addModal.classList.add('hidden');
            editModal.classList.add('hidden');
            deleteModal.classList.add('hidden');
        });
    });
    
    // Password Matching Validation (Add User Form)
    const addForm = document.getElementById('add-user-form');
    const password = document.getElementById('password');
    const confirmPassword = document.getElementById('confirm_password');
    const passwordError = document.getElementById('password-match-error');
    
    if (addForm) {
        addForm.addEventListener('submit', function(e) {
            if (password.value !== confirmPassword.value) {
                passwordError.classList.remove('hidden');
                e.preventDefault();
            } else {
                passwordError.classList.add('hidden');
            }
        });
    }
    
    // Password Matching Validation (Edit User Form)
    const editForm = document.getElementById('edit-user-form');
    const editPassword = document.getElementById('edit-password');
    const editConfirmPassword = document.getElementById('edit-confirm-password');
    const editPasswordError = document.getElementById('edit-password-match-error');
    
    if (editForm) {
        editForm.addEventListener('submit', function(e) {
            if (editPassword.value && editPassword.value !== editConfirmPassword.value) {
                editPasswordError.classList.remove('hidden');
                e.preventDefault();
            } else {
                editPasswordError.classList.add('hidden');
            }
        });
    }
    
    // Edit User
    editBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const userId = this.getAttribute('data-id');
            
            // Fetch user data with AJAX
            fetch(`/api/v1/users/${userId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const user = data.user;
                        
                        // Populate form fields
                        document.getElementById('edit-user-id').value = user.id;
                        document.getElementById('edit-username').value = user.username;
                        document.getElementById('edit-fullname').value = user.fullname || '';
                        document.getElementById('edit-email').value = user.email;
                        document.getElementById('edit-is-admin').checked = user.is_admin;
                        
                        // Clear password fields
                        document.getElementById('edit-password').value = '';
                        document.getElementById('edit-confirm-password').value = '';
                        
                        // Update form action
                        document.getElementById('edit-user-form').action = "/users/" + user.id + "/update";
                        
                        // Show modal
                        editModal.classList.remove('hidden');
                    } else {
                        showToast('Error loading user data', 'error');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showToast('Error loading user data', 'error');
                });
        });
    });
    
    // Delete User
    deleteBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const userId = this.getAttribute('data-id');
            const username = this.closest('tr').querySelector('td:first-child').textContent.trim();
            
            // Set user ID and name
            document.getElementById('delete-user-id').value = userId;
            document.getElementById('delete-user-name').textContent = username;
            
            // Update form action
            document.getElementById('delete-user-form').action = "/users/" + userId + "/delete";
            
            // Show modal
            deleteModal.classList.remove('hidden');
        });
    });
    
    if (cancelDeleteBtn) {
        cancelDeleteBtn.addEventListener('click', function() {
            deleteModal.classList.add('hidden');
        });
    }
    
    // Close modals when clicking outside
    window.addEventListener('click', function(e) {
        if (e.target === addModal) {
            addModal.classList.add('hidden');
        } else if (e.target === editModal) {
            editModal.classList.add('hidden');
        } else if (e.target === deleteModal) {
            deleteModal.classList.add('hidden');
        }
    });
});

// Function to show toast/notification messages - removed as we now use the central toast.js 