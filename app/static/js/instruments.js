class InstrumentManager {
    constructor() {
        this.selectedInstruments = [];
        this.init();
    }

    init() {
        this.loadSavedInstruments();
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Manual entry form
        const tokenInput = document.getElementById('instrument-token');
        const nameInput = document.getElementById('instrument-name');

        if (tokenInput) {
            tokenInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') this.addManualInstrument();
            });
        }

        if (nameInput) {
            nameInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') this.addManualInstrument();
            });
        }
    }

    loadSavedInstruments() {
        const saved = localStorage.getItem('selectedInstruments');
        if (saved) {
            try {
                this.selectedInstruments = JSON.parse(saved);
                this.updateInstrumentsList();
            } catch (error) {
                console.error('Error loading saved instruments:', error);
                this.selectedInstruments = [];
            }
        }
    }

    saveInstruments() {
        try {
            localStorage.setItem('selectedInstruments', JSON.stringify(this.selectedInstruments));
        } catch (error) {
            console.error('Error saving instruments:', error);
        }
    }

    addInstrument(token, exchange, name) {
        if (!token || !exchange) {
            this.showMessage('Invalid instrument data', 'error');
            return false;
        }

        const exists = this.selectedInstruments.some(inst =>
            inst.instrument_token === token && inst.exchange_segment === exchange);

        if (exists) {
            this.showMessage('Instrument already selected', 'warning');
            return false;
        }

        this.selectedInstruments.push({
            instrument_token: token,
            exchange_segment: exchange,
            name: name || token
        });

        this.updateInstrumentsList();
        this.saveInstruments();
        this.showMessage(`Added ${name || token}`, 'success');
        return true;
    }

    addManualInstrument() {
        const token = document.getElementById('instrument-token').value.trim();
        const exchange = document.getElementById('exchange-segment').value;
        const name = document.getElementById('instrument-name').value.trim() || token;

        if (!token) {
            this.showMessage('Please enter an instrument token', 'error');
            return;
        }

        if (this.addInstrument(token, exchange, name)) {
            document.getElementById('instrument-token').value = '';
            document.getElementById('instrument-name').value = '';
        }
    }

    addPresetInstrument(token, exchange, name) {
        this.addInstrument(token, exchange, name);
    }

    removeInstrument(token, exchange) {
        this.selectedInstruments = this.selectedInstruments.filter(inst =>
            !(inst.instrument_token === token && inst.exchange_segment === exchange));
        this.updateInstrumentsList();
        this.saveInstruments();
        this.showMessage('Instrument removed', 'info');
    }

    clearAllInstruments() {
        if (this.selectedInstruments.length === 0) return;

        if (confirm('Are you sure you want to clear all selected instruments?')) {
            this.selectedInstruments = [];
            this.updateInstrumentsList();
            this.saveInstruments();
            this.showMessage('All instruments cleared', 'info');
        }
    }

    updateInstrumentsList() {
        const listDiv = document.getElementById('instruments-list');
        const countBadge = document.getElementById('instrument-count');

        if (!listDiv || !countBadge) return;

        countBadge.textContent = this.selectedInstruments.length;

        if (this.selectedInstruments.length === 0) {
            listDiv.innerHTML = `
                <div class="empty-state">
                    <div class="material-icons">inventory_2</div>
                    <p>No instruments selected</p>
                </div>
            `;
            return;
        }

        listDiv.innerHTML = this.selectedInstruments.map(inst => `
            <div class="instrument-item" data-token="${inst.instrument_token}" data-exchange="${inst.exchange_segment}">
                <span>
                    <span class="material-icons" style="font-size: 16px; margin-right: 8px; vertical-align: middle;">show_chart</span>
                    ${inst.name} (${inst.instrument_token}) - ${this.getExchangeName(inst.exchange_segment)}
                </span>
                <button onclick="window.instrumentManager.removeInstrument('${inst.instrument_token}', '${inst.exchange_segment}')">
                    <span class="material-icons" style="font-size: 16px;">remove</span>
                    Remove
                </button>
            </div>
        `).join('');
    }

    getExchangeName(segment) {
        const names = {
            'nse_cm': 'NSE Cash Market',
            'bse_cm': 'BSE Cash Market',
            'nse_fo': 'NSE F&O',
            'bse_fo': 'BSE F&O',
            'cde_fo': 'Currency Derivatives',
            'mcx_fo': 'MCX Derivatives'
        };
        return names[segment] || segment;
    }

    showMessage(text, type = 'info', duration = 3000) {
        const messageDiv = document.getElementById('message');
        if (!messageDiv) return;

        const iconMap = {
            success: 'check_circle',
            error: 'error',
            warning: 'warning',
            info: 'info'
        };

        const colorMap = {
            success: '#4CAF50',
            error: '#f44336',
            warning: '#ff9800',
            info: '#2196F3'
        };

        messageDiv.innerHTML = `
            <div style="background: linear-gradient(135deg, ${colorMap[type]}20, ${colorMap[type]}10);
                        color: ${colorMap[type]};
                        padding: 15px 20px;
                        border-radius: 12px;
                        margin: 15px 0;
                        border: 1px solid ${colorMap[type]}30;
                        backdrop-filter: blur(10px);
                        display: flex;
                        align-items: center;
                        gap: 8px;">
                <span class="material-icons">${iconMap[type]}</span>
                ${text}
            </div>
        `;

        if (duration > 0) {
            setTimeout(() => {
                messageDiv.innerHTML = '';
            }, duration);
        }
    }

    goBack() {
        window.location.href = '/';
    }

    saveAndContinue() {
        if (this.selectedInstruments.length === 0) {
            this.showMessage('Please select at least one instrument before continuing', 'error');
            return;
        }

        this.saveInstruments();
        this.showMessage('Instruments saved successfully! Redirecting to main page...', 'success', 1500);

        setTimeout(() => {
            window.location.href = '/';
        }, 1500);
    }

    async validateInstruments() {
        try {
            const response = await fetch('/api/instruments/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(this.selectedInstruments)
            });

            const result = await response.json();

            if (result.invalid_count > 0) {
                this.showMessage(
                    `Warning: ${result.invalid_count} instruments may not be valid`,
                    'warning',
                    5000
                );
            } else {
                this.showMessage('All instruments validated successfully', 'success');
            }

            return result;
        } catch (error) {
            console.error('Validation error:', error);
            this.showMessage('Unable to validate instruments', 'warning');
            return null;
        }
    }
}

// Global functions for onclick handlers
function addInstrument() {
    if (window.instrumentManager) {
        window.instrumentManager.addManualInstrument();
    }
}

function addPresetInstrument(token, exchange, name) {
    if (window.instrumentManager) {
        window.instrumentManager.addPresetInstrument(token, exchange, name);
    }
}

function clearAllInstruments() {
    if (window.instrumentManager) {
        window.instrumentManager.clearAllInstruments();
    }
}

function goBack() {
    if (window.instrumentManager) {
        window.instrumentManager.goBack();
    }
}

function saveAndContinue() {
    if (window.instrumentManager) {
        window.instrumentManager.saveAndContinue();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.instrumentManager = new InstrumentManager();
});