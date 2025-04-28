// frontend/static/js/script.js
document.addEventListener('DOMContentLoaded', function() {
    // Common elements
    const notificationCount = document.getElementById('notificationCount');
    
    // Update notification count on all pages
    function updateNotificationCount() {
        fetch('/api/notifications')
            .then(response => response.json())
            .then(data => {
                notificationCount.textContent = data.length;
            })
            .catch(error => {
                console.error('Error fetching notifications:', error);
            });
    }
    
    // Initialize based on current page
    if (document.getElementById('schemeForm')) {
        // Index page functionality
        const schemeForm = document.getElementById('schemeForm');
        const trainModelBtn = document.getElementById('trainModelBtn');
        
        schemeForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const title = document.getElementById('schemeTitle').value;
            const description = document.getElementById('schemeDescription').value;
            
            fetch('/api/schemes', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ title, description })
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('formResult').innerHTML = `
                    <div class="alert alert-success">
                        Scheme added successfully! Category: ${data.category}
                    </div>
                `;
                schemeForm.reset();
                updateNotificationCount();
            })
            .catch(error => {
                document.getElementById('formResult').innerHTML = `
                    <div class="alert alert-danger">
                        Error: ${error.message}
                    </div>
                `;
            });
        });
        
        trainModelBtn.addEventListener('click', function() {
            fetch('/api/train-model', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('trainingResult').innerHTML = `
                    <div class="alert alert-success">
                        ${data.message}
                    </div>
                `;
            })
            .catch(error => {
                document.getElementById('trainingResult').innerHTML = `
                    <div class="alert alert-danger">
                        Error: ${error.message}
                    </div>
                `;
            });
        });
    }
    
    if (document.getElementById('schemesContainer')) {
        // Schemes page functionality
        const schemesContainer = document.getElementById('schemesContainer');
        const categoryFilter = document.getElementById('categoryFilter');
        
        function loadSchemes(category = '') {
            let url = '/api/schemes';
            if (category) {
                url += `?category=${encodeURIComponent(category)}`;
            }
            
            fetch(url)
                .then(response => response.json())
                .then(schemes => {
                    if (schemes.length === 0) {
                        schemesContainer.innerHTML = `
                            <div class="col-12">
                                <div class="alert alert-info">No schemes found</div>
                            </div>
                        `;
                        return;
                    }
                    
                    // Update category filter options
                    if (categoryFilter.options.length <= 1) {
                        const categories = [...new Set(schemes.map(s => s.category))];
                        categories.forEach(cat => {
                            const option = document.createElement('option');
                            option.value = cat;
                            option.textContent = cat;
                            categoryFilter.appendChild(option);
                        });
                    }
                    
                    // Display schemes
                    let html = '';
                    schemes.forEach(scheme => {
                        html += `
                            <div class="col-md-4 mb-4">
                                <div class="card h-100">
                                    <div class="card-body">
                                        <span class="badge bg-primary">${scheme.category}</span>
                                        <h5 class="card-title mt-2">${scheme.title}</h5>
                                        <p class="card-text">${scheme.description.substring(0, 100)}...</p>
                                        <small class="text-muted">Published: ${scheme.publish_date || 'N/A'}</small>
                                    </div>
                                </div>
                            </div>
                        `;
                    });
                    schemesContainer.innerHTML = html;
                })
                .catch(error => {
                    schemesContainer.innerHTML = `
                        <div class="col-12">
                            <div class="alert alert-danger">Error loading schemes: ${error.message}</div>
                        </div>
                    `;
                });
        }
        
        categoryFilter.addEventListener('change', function() {
            loadSchemes(this.value);
        });
        
        // Initial load
        loadSchemes();
    }
    
    // Initialize notification count
    updateNotificationCount();
});