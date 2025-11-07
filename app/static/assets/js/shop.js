// Shop Page Interactive JavaScript
document.addEventListener('DOMContentLoaded', function() {
    
    // ===== CATEGORY FILTER =====
    const categoryFilters = document.querySelectorAll('.category-filter');
    categoryFilters.forEach(filter => {
        filter.addEventListener('click', function(e) {
            e.preventDefault();
            const categoryId = this.dataset.category;
            const currentUrl = new URL(window.location.href);
            
            if (categoryId === 'all') {
                currentUrl.searchParams.delete('category');
            } else {
                currentUrl.searchParams.set('category', categoryId);
            }
            currentUrl.searchParams.delete('page'); // Reset to page 1
            
            window.location.href = currentUrl.toString();
        });
    });

    // ===== SORT DROPDOWN =====
    const sortSelect = document.getElementById('sort-select');
    if (sortSelect) {
        sortSelect.addEventListener('change', function() {
            const sortValue = this.value;
            const currentUrl = new URL(window.location.href);
            
            if (sortValue) {
                currentUrl.searchParams.set('sort', sortValue);
            } else {
                currentUrl.searchParams.delete('sort');
            }
            currentUrl.searchParams.delete('page'); // Reset to page 1
            
            window.location.href = currentUrl.toString();
        });
    }

    // ===== VIEW MODE TOGGLE (Grid/List) =====
    const gridBtn = document.querySelector('[data-view="grid"]');
    const listBtn = document.querySelector('[data-view="list"]');
    const productContainer = document.querySelector('.product-container');
    
    if (gridBtn && listBtn && productContainer) {
        gridBtn.addEventListener('click', function() {
            productContainer.classList.remove('list-view');
            productContainer.classList.add('grid-view');
            gridBtn.classList.add('active');
            listBtn.classList.remove('active');
            localStorage.setItem('shopView', 'grid');
        });

        listBtn.addEventListener('click', function() {
            productContainer.classList.remove('grid-view');
            productContainer.classList.add('list-view');
            listBtn.classList.add('active');
            gridBtn.classList.remove('active');
            localStorage.setItem('shopView', 'list');
        });

        // Restore saved view preference
        const savedView = localStorage.getItem('shopView') || 'grid';
        if (savedView === 'list') {
            listBtn.click();
        }
    }

    // ===== PRODUCT CARD ANIMATIONS =====
    const productCards = document.querySelectorAll('.bz-season-item, .bz-shop-item-list');
    
    // Intersection Observer for fade-in animation
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    productCards.forEach(card => {
        card.classList.add('fade-ready');
        observer.observe(card);
    });

    // ===== ADD TO CART ANIMATION =====
    const addToCartBtns = document.querySelectorAll('.bz-season-item-hover-cart a, .bz-shop-item-list-content-cart');
    
    addToCartBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            // Don't prevent default - let the link work
            // Add visual feedback
            this.classList.add('btn-clicked');
            
            // Create floating feedback
            const feedback = document.createElement('div');
            feedback.className = 'cart-feedback';
            feedback.innerHTML = '<i class="fas fa-check"></i> Ajouté !';
            this.parentElement.appendChild(feedback);
            
            setTimeout(() => {
                feedback.remove();
            }, 2000);
            
            setTimeout(() => {
                this.classList.remove('btn-clicked');
            }, 300);
        });
    });

    // ===== PRICE RANGE SLIDER (if exists) =====
    const priceSlider = document.getElementById('shop-slider-range');
    if (priceSlider && typeof $.ui !== 'undefined') {
        const minPrice = parseInt(priceSlider.dataset.min || 0);
        const maxPrice = parseInt(priceSlider.dataset.max || 1000000);
        
        $("#shop-slider-range").slider({
            range: true,
            min: minPrice,
            max: maxPrice,
            values: [minPrice, maxPrice],
            slide: function(event, ui) {
                $("#s-amount").val(ui.values[0] + " - " + ui.values[1] + " FCFA");
            },
            stop: function(event, ui) {
                // Apply filter
                const currentUrl = new URL(window.location.href);
                currentUrl.searchParams.set('min_price', ui.values[0]);
                currentUrl.searchParams.set('max_price', ui.values[1]);
                currentUrl.searchParams.delete('page');
                
                window.location.href = currentUrl.toString();
            }
        });
    }

    // ===== HIGHLIGHT ACTIVE CATEGORY =====
    const currentCategory = new URLSearchParams(window.location.search).get('category');
    if (currentCategory) {
        document.querySelectorAll('.category-filter').forEach(filter => {
            if (filter.dataset.category === currentCategory) {
                filter.classList.add('active');
            } else {
                filter.classList.remove('active');
            }
        });
    } else {
        // Highlight "All" if no category selected
        const allFilter = document.querySelector('.category-filter[data-category="all"]');
        if (allFilter) allFilter.classList.add('active');
    }

    // ===== SET ACTIVE SORT =====
    const currentSort = new URLSearchParams(window.location.search).get('sort');
    if (sortSelect && currentSort) {
        sortSelect.value = currentSort;
    }

    // ===== IMAGE LAZY LOADING FALLBACK =====
    const images = document.querySelectorAll('.bz-season-item-img img, .bz-shop-item-list-img img');
    images.forEach(img => {
        img.addEventListener('error', function() {
            // If image fails to load, use placeholder
            const placeholders = [
                '/static/assets/img/shop/shop-1.jpg',
                '/static/assets/img/shop/shop-2.jpg',
                '/static/assets/img/shop/shop-3.jpg',
                '/static/assets/img/shop/armoir.jpeg',
                '/static/assets/img/shop/meublee.jpeg'
            ];
            const randomPlaceholder = placeholders[Math.floor(Math.random() * placeholders.length)];
            this.src = randomPlaceholder;
        });
    });

    // ===== SMOOTH SCROLL FOR PAGINATION =====
    const paginationLinks = document.querySelectorAll('.bz-shop-paginate a');
    paginationLinks.forEach(link => {
        link.addEventListener('click', function() {
            const shopTop = document.querySelector('.bz-shop-area');
            if (shopTop) {
                window.scrollTo({
                    top: shopTop.offsetTop - 100,
                    behavior: 'smooth'
                });
            }
        });
    });

    // ===== PRODUCT COUNT ANIMATION =====
    const productCount = document.querySelector('.product-count');
    if (productCount) {
        const count = parseInt(productCount.textContent);
        let start = 0;
        const duration = 1000;
        const increment = count / (duration / 16);
        
        const counter = setInterval(() => {
            start += increment;
            if (start >= count) {
                productCount.textContent = count;
                clearInterval(counter);
            } else {
                productCount.textContent = Math.floor(start);
            }
        }, 16);
    }

    // ===== QUICK VIEW MODAL (if implemented later) =====
    const quickViewBtns = document.querySelectorAll('.eye-popup-product');
    quickViewBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            // Placeholder for quick view functionality
            console.log('Quick view clicked');
        });
    });

});
