class InstrumentAutocomplete {
    constructor(searchInputId, dropdownId) {
        this.searchInput = document.getElementById(searchInputId);
        this.dropdown = document.getElementById(dropdownId);
        this.timeout = null;
        this.selectedIndex = -1;
        this.init();
    }

    init() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        this.searchInput.addEventListener('input', (e) => this.handleInput(e));
        this.searchInput.addEventListener('keydown', (e) => this.handleKeydown(e));
        this.searchInput.addEventListener('blur', () => this.handleBlur());

        document.addEventListener('click', (e) => this.handleDocumentClick(e));
    }

    handleInput(e) {
        const query = e.target.value.trim();

        clearTimeout(this.timeout);

        if (query.length < 2) {
            this.hide();
            return;
        }

        this.timeout = setTimeout(async () => {
            const items = await this.fetchSuggestions(query);
            this.show(items);
        }, 300);
    }

    handleKeydown(e) {
        if (this.dropdown.style.display === 'none') return;

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                this.navigate('down');
                break;
            case 'ArrowUp':
                e.preventDefault();
                this.navigate('up');
                break;
            case 'Enter':
                e.preventDefault();
                this.selectCurrent();
                break;
            case 'Escape':
                this.hide();
                break;
        }
    }

    handleBlur() {
        setTimeout(() => this.hide(), 200);
    }

    handleDocumentClick(e) {
        if (!e.target.closest('.search-container')) {
            this.hide();
        }
    }

    async fetchSuggestions(query) {
        try {
            const response = await fetch(`/api/instruments/autocomplete?query=${encodeURIComponent(query)}&limit=8`);
            if (!response.ok) throw new Error('Network response was not ok');
            return await response.json();
        } catch (error) {
            console.error('Autocomplete fetch error:', error);
            return [];
        }
    }

    show(items) {
        if (items.length === 0) {
            this.hide();
            return;
        }

        this.dropdown.innerHTML = items.map((item, index) => `
            <div class="autocomplete-item"
                 data-index="${index}"
                 data-token="${item.token}"
                 data-exchange="${item.exchange}"
                 data-label="${item.label}">
                <div class="symbol">${item.label.split(' - ')[0]}</div>
                <div class="company-name">${item.label.split(' - ')[1]?.split(' (')[0] || ''}</div>
                <div class="exchange-info">
                    <span>Token: ${item.token}</span>
                    <span>${item.exchange.toUpperCase()}</span>
                    ${item.sector ? `<span class="sector">${item.sector}</span>` : ''}
                </div>
            </div>
        `).join('');

        // Add click listeners to items
        this.dropdown.querySelectorAll('.autocomplete-item').forEach(item => {
            item.addEventListener('click', () => this.selectItem(item));
        });

        this.dropdown.style.display = 'block';
        this.selectedIndex = -1;
    }

    hide() {
        this.dropdown.style.display = 'none';
        this.selectedIndex = -1;
    }

    navigate(direction) {
        const items = this.dropdown.querySelectorAll('.autocomplete-item');
        if (items.length === 0) return;

        if (this.selectedIndex >= 0) {
            items[this.selectedIndex].classList.remove('selected');
        }

        if (direction === 'down') {
            this.selectedIndex = (this.selectedIndex + 1) % items.length;
        } else if (direction === 'up') {
            this.selectedIndex = this.selectedIndex <= 0 ? items.length - 1 : this.selectedIndex - 1;
        }

        items[this.selectedIndex].classList.add('selected');
        this.scrollToSelected();
    }

    scrollToSelected() {
        const selectedItem = this.dropdown.querySelector('.autocomplete-item.selected');
        if (selectedItem) {
            selectedItem.scrollIntoView({ block: 'nearest' });
        }
    }

    selectCurrent() {
        const selectedItem = this.dropdown.querySelector('.autocomplete-item.selected');
        if (selectedItem) {
            this.selectItem(selectedItem);
        }
    }

    selectItem(item) {
        const token = item.dataset.token;
        const exchange = item.dataset.exchange;
        const label = item.dataset.label;

        const symbolName = label.split(' - ')[0];
        const companyName = label.split(' - ')[1]?.split(' (')[0] || symbolName;

        if (window.instrumentManager) {
            window.instrumentManager.addInstrument(token, exchange, companyName);
        }

        this.hide();
        this.searchInput.value = '';
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('instrument-search')) {
        window.autocomplete = new InstrumentAutocomplete('instrument-search', 'autocomplete-dropdown');
    }
});