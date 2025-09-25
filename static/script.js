class BankStatementComparison {
    constructor() {
        this.tables = new Map();
        this.processingQueue = [];
        this.isProcessing = false;
        this.maxTables = 4;
        this.dropZoneCollapsed = true;
        this.dragCounter = 0;
        this.init();
    }

    init() {
        this.setupDropZone();
        this.setupClearButtons();
        this.setupClearAllButton();
        this.setupToggleDropZone();
        this.setupFullPageDrop();
        this.initializeDropZoneState();
        this.updateDropZoneState();
        this.updateTableStatuses();
    }

    setupToggleDropZone() {
        const toggleButton = document.getElementById('toggleDropZone');
        const dropZoneContainer = document.getElementById('dropZoneContainer');
        const toggleIcon = toggleButton.querySelector('.toggle-icon');
        
        toggleButton.addEventListener('click', () => {
            this.dropZoneCollapsed = !this.dropZoneCollapsed;
            
            if (this.dropZoneCollapsed) {
                dropZoneContainer.classList.add('collapsed');
                toggleButton.innerHTML = `
                    <svg class="toggle-icon rotated" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <polyline points="6,9 12,15 18,9"/>
                    </svg>
                    Show Drop Zone
                `;
            } else {
                dropZoneContainer.classList.remove('collapsed');
                toggleButton.innerHTML = `
                    <svg class="toggle-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <polyline points="6,9 12,15 18,9"/>
                    </svg>
                    Hide Drop Zone
                `;
            }
        });
    }

    initializeDropZoneState() {
        const dropZoneContainer = document.getElementById('dropZoneContainer');
        const toggleButton = document.getElementById('toggleDropZone');
        
        // Set initial collapsed state
        dropZoneContainer.classList.add('collapsed');
        toggleButton.innerHTML = `
            <svg class="toggle-icon rotated" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <polyline points="6,9 12,15 18,9"/>
            </svg>
            Show Drop Zone
        `;
    }

    setupFullPageDrop() {
        const dropModal = document.getElementById('dropModal');
        const dropModalStatus = document.getElementById('dropModalStatus');
        
        // Prevent default drag behavior on document
        document.addEventListener('dragenter', (e) => {
            e.preventDefault();
            this.dragCounter++;
            
            // Only show modal if dragging files and not already over the main drop zone
            if (this.dragCounter === 1 && !e.target.closest('.drop-zone')) {
                this.showDropModal();
            }
        });
        
        document.addEventListener('dragleave', (e) => {
            e.preventDefault();
            this.dragCounter--;
            
            if (this.dragCounter === 0) {
                this.hideDropModal();
            }
        });
        
        document.addEventListener('dragover', (e) => {
            e.preventDefault();
            
            // Update modal status based on availability
            if (dropModal.classList.contains('active')) {
                const availableSlots = this.getAvailableTableSlots();
                const hasProcessingItems = this.processingQueue.some(item => 
                    item.status === 'queued' || item.status === 'processing'
                );
                
                if (availableSlots.length === 0 && !hasProcessingItems) {
                    dropModalStatus.textContent = 'All tables are full - clear some tables first';
                    dropModalStatus.style.backgroundColor = 'rgba(239, 68, 68, 0.2)';
                    dropModalStatus.style.borderColor = 'rgba(239, 68, 68, 0.3)';
                } else {
                    dropModalStatus.textContent = `${availableSlots.length} table${availableSlots.length !== 1 ? 's' : ''} available`;
                    dropModalStatus.style.backgroundColor = 'rgba(16, 185, 129, 0.2)';
                    dropModalStatus.style.borderColor = 'rgba(16, 185, 129, 0.3)';
                }
            }
        });
        
        document.addEventListener('drop', (e) => {
            e.preventDefault();
            this.dragCounter = 0;
            this.hideDropModal();
            
            // Only handle drop if not over the main drop zone
            if (!e.target.closest('.drop-zone')) {
                const files = Array.from(e.dataTransfer.files);
                this.handleFileUpload(files);
            }
        });
    }
    
    showDropModal() {
        const dropModal = document.getElementById('dropModal');
        const dropModalStatus = document.getElementById('dropModalStatus');
        
        const availableSlots = this.getAvailableTableSlots();
        const hasProcessingItems = this.processingQueue.some(item => 
            item.status === 'queued' || item.status === 'processing'
        );
        
        if (availableSlots.length === 0 && !hasProcessingItems) {
            dropModalStatus.textContent = 'All tables are full - clear some tables first';
            dropModalStatus.style.backgroundColor = 'rgba(239, 68, 68, 0.2)';
            dropModalStatus.style.borderColor = 'rgba(239, 68, 68, 0.3)';
        } else {
            dropModalStatus.textContent = `${availableSlots.length} table${availableSlots.length !== 1 ? 's' : ''} available`;
            dropModalStatus.style.backgroundColor = 'rgba(16, 185, 129, 0.2)';
            dropModalStatus.style.borderColor = 'rgba(16, 185, 129, 0.3)';
        }
        
        dropModal.classList.add('active');
    }
    
    hideDropModal() {
        const dropModal = document.getElementById('dropModal');
        dropModal.classList.remove('active');
    }

    setupDropZone() {
        const dropZone = document.getElementById('mainDropZone');
        const fileInput = document.getElementById('fileInput');
        
        // Click to browse
        dropZone.addEventListener('click', () => {
            if (!dropZone.classList.contains('disabled')) {
                fileInput.click();
            }
        });

        // File input change
        fileInput.addEventListener('change', (e) => {
            const files = Array.from(e.target.files);
            if (files.length > 0) {
                this.handleFileUpload(files);
                fileInput.value = ''; // Reset input
            }
        });

        // Drag and drop events
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            if (!dropZone.classList.contains('disabled')) {
                dropZone.classList.add('dragover');
            }
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            
            if (!dropZone.classList.contains('disabled')) {
                const files = Array.from(e.dataTransfer.files);
                this.handleFileUpload(files);
            }
        });
    }

    setupClearButtons() {
        const clearButtons = document.querySelectorAll('.btn-clear');
        
        clearButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.stopPropagation();
                const tableNumber = button.dataset.table;
                this.clearTable(tableNumber);
            });
        });
    }

    setupClearAllButton() {
        const clearAllButton = document.getElementById('clearAll');
        clearAllButton.addEventListener('click', () => {
            this.clearAllTables();
        });
    }

    handleFileUpload(files) {
        const availableSlots = this.getAvailableTableSlots();
        const pdfFiles = files.filter(file => file.type === 'application/pdf');
        
        if (pdfFiles.length === 0) {
            this.showNotification('Please upload PDF files only', 'error');
            return;
        }
        
        const filesToProcess = pdfFiles.slice(0, availableSlots.length);
        
        if (filesToProcess.length === 0) {
            this.showNotification('All tables are full. Please clear some tables first.', 'warning');
            return;
        }

        if (pdfFiles.length > filesToProcess.length) {
            this.showNotification(`Only processing ${filesToProcess.length} files. ${pdfFiles.length - filesToProcess.length} files skipped (no available tables).`, 'warning');
        }
        
        if (files.length > pdfFiles.length) {
            const nonPdfCount = files.length - pdfFiles.length;
            this.showNotification(`${nonPdfCount} non-PDF file${nonPdfCount !== 1 ? 's' : ''} ignored. Only PDF files are supported.`, 'warning');
        }

        // Add files to processing queue
        filesToProcess.forEach((file, index) => {
            const targetTable = availableSlots[index];
            const queueItem = {
                id: Date.now() + index,
                file: file,
                targetTable: targetTable,
                status: 'queued',
                fileName: file.name
            };
            
            this.processingQueue.push(queueItem);
            this.addQueueItem(queueItem);
            this.updateTableStatus(targetTable, 'processing');
        });

        this.updateDropZoneState();
        this.processQueue();
    }

    getAvailableTableSlots() {
        const availableSlots = [];
        for (let i = 1; i <= this.maxTables; i++) {
            if (!this.tables.has(i.toString()) && !this.isTableBeingProcessed(i.toString())) {
                availableSlots.push(i.toString());
            }
        }
        return availableSlots;
    }

    isTableBeingProcessed(tableNumber) {
        return this.processingQueue.some(item => 
            item.targetTable === tableNumber && 
            (item.status === 'queued' || item.status === 'processing')
        );
    }

    async processQueue() {
        if (this.isProcessing || this.processingQueue.length === 0) {
            return;
        }

        this.isProcessing = true;
        this.showProcessingQueue();

        // Get all queued items and process them simultaneously
        const queuedItems = this.processingQueue.filter(item => item.status === 'queued');
        
        if (queuedItems.length === 0) {
            this.isProcessing = false;
            return;
        }
        
        // Mark all items as processing
        queuedItems.forEach(item => {
            item.status = 'processing';
            this.updateQueueItem(item);
        });
        
        // Process all items simultaneously
        const processingPromises = queuedItems.map(async (queueItem) => {
            try {
                const data = await this.processStatementAPI(queueItem.file, queueItem.targetTable);
                
                // Populate table with results
                this.populateTable(queueItem.targetTable, data, queueItem.fileName);
                
                queueItem.status = 'completed';
                this.updateQueueItem(queueItem);
                this.updateTableStatus(queueItem.targetTable, 'populated');
                
            } catch (error) {
                console.error('Error processing file:', error);
                queueItem.status = 'error';
                queueItem.error = error.message;
                this.updateQueueItem(queueItem);
                this.updateTableStatus(queueItem.targetTable, 'error');
            }
            
            // Remove completed/error items after a delay
            setTimeout(() => {
                this.removeQueueItem(queueItem.id);
            }, 2000);
        });
        
        // Wait for all processing to complete
        await Promise.allSettled(processingPromises);

        this.isProcessing = false;
        this.updateDropZoneState();
        
        // Hide processing queue if empty
        setTimeout(() => {
            if (this.processingQueue.length === 0) {
                this.hideProcessingQueue();
            }
        }, 3000);
    }

    showProcessingQueue() {
        const queueElement = document.getElementById('processingQueue');
        queueElement.style.display = 'block';
        this.updateQueueCount();
    }

    hideProcessingQueue() {
        const queueElement = document.getElementById('processingQueue');
        queueElement.style.display = 'none';
    }

    addQueueItem(queueItem) {
        const queueItems = document.getElementById('queueItems');
        const itemElement = document.createElement('div');
        itemElement.className = 'queue-item';
        itemElement.id = `queue-item-${queueItem.id}`;
        
        itemElement.innerHTML = `
            <div class="queue-item-spinner"></div>
            <div class="queue-item-info">
                <div class="queue-item-name">${queueItem.fileName}</div>
                <div class="queue-item-status">Queued for processing</div>
            </div>
            <div class="queue-item-target">→ Table ${queueItem.targetTable}</div>
        `;
        
        queueItems.appendChild(itemElement);
        this.updateQueueCount();
    }

    updateQueueItem(queueItem) {
        const itemElement = document.getElementById(`queue-item-${queueItem.id}`);
        if (!itemElement) return;

        const statusElement = itemElement.querySelector('.queue-item-status');
        const iconElement = itemElement.querySelector('.queue-item-spinner, .queue-item-icon');
        
        itemElement.className = `queue-item ${queueItem.status}`;
        
        switch (queueItem.status) {
            case 'processing':
                statusElement.textContent = 'Processing...';
                break;
            case 'completed':
                statusElement.textContent = 'Completed successfully';
                iconElement.outerHTML = `
                    <svg class="queue-item-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" style="color: var(--success-color);">
                        <path d="M20 6L9 17l-5-5"/>
                    </svg>
                `;
                break;
            case 'error':
                statusElement.textContent = `Error: ${queueItem.error || 'Processing failed'}`;
                iconElement.outerHTML = `
                    <svg class="queue-item-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" style="color: var(--error-color);">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="15" y1="9" x2="9" y2="15"/>
                        <line x1="9" y1="9" x2="15" y2="15"/>
                    </svg>
                `;
                break;
        }
    }

    removeQueueItem(queueItemId) {
        const itemElement = document.getElementById(`queue-item-${queueItemId}`);
        if (itemElement) {
            itemElement.style.opacity = '0';
            itemElement.style.transform = 'translateX(100%)';
            setTimeout(() => {
                itemElement.remove();
                this.updateQueueCount();
            }, 300);
        }
        
        // Remove from queue array
        this.processingQueue = this.processingQueue.filter(item => item.id !== queueItemId);
    }

    updateQueueCount() {
        const queueCount = document.getElementById('queueCount');
        const activeItems = this.processingQueue.filter(item => 
            item.status === 'queued' || item.status === 'processing'
        ).length;
        
        queueCount.textContent = `${activeItems} file${activeItems !== 1 ? 's' : ''} in queue`;
    }

    updateDropZoneState() {
        const dropZone = document.getElementById('mainDropZone');
        const dropText = dropZone.querySelector('.drop-text');
        const dropSubtext = dropZone.querySelector('.drop-subtext');
        const clearAllButton = document.getElementById('clearAll');
        
        const availableSlots = this.getAvailableTableSlots();
        const hasProcessingItems = this.processingQueue.some(item => 
            item.status === 'queued' || item.status === 'processing'
        );
        
        if (availableSlots.length === 0 && !hasProcessingItems) {
            // All tables full
            dropZone.classList.add('disabled');
            dropText.textContent = 'All Tables Full';
            dropSubtext.textContent = 'Clear some tables to upload more files';
            clearAllButton.disabled = false;
        } else if (hasProcessingItems) {
            // Currently processing
            dropZone.classList.remove('disabled');
            dropText.textContent = 'Processing Files...';
            dropSubtext.textContent = `${availableSlots.length} table${availableSlots.length !== 1 ? 's' : ''} still available`;
            clearAllButton.disabled = true;
        } else {
            // Normal state
            dropZone.classList.remove('disabled');
            dropText.textContent = 'Drop Bank Statement PDFs Here';
            dropSubtext.textContent = `or click to browse • ${availableSlots.length} table${availableSlots.length !== 1 ? 's' : ''} available • Multiple files supported`;
            clearAllButton.disabled = false;
        }
    }

    updateTableStatuses() {
        for (let i = 1; i <= this.maxTables; i++) {
            const tableNumber = i.toString();
            if (this.tables.has(tableNumber)) {
                this.updateTableStatus(tableNumber, 'populated');
            } else if (this.isTableBeingProcessed(tableNumber)) {
                this.updateTableStatus(tableNumber, 'processing');
            } else {
                this.updateTableStatus(tableNumber, 'empty');
            }
        }
    }

    updateTableStatus(tableNumber, status) {
        const statusElement = document.getElementById(`status-${tableNumber}`);
        const clearButton = document.querySelector(`.btn-clear[data-table="${tableNumber}"]`);
        
        statusElement.className = `status-indicator ${status}`;
        
        switch (status) {
            case 'empty':
                statusElement.textContent = 'Empty';
                clearButton.disabled = true;
                break;
            case 'processing':
                statusElement.textContent = 'Processing...';
                clearButton.disabled = true;
                break;
            case 'populated':
                statusElement.textContent = 'Populated';
                clearButton.disabled = false;
                break;
            case 'error':
                statusElement.textContent = 'Error';
                clearButton.disabled = false;
                break;
        }
    }

    async processStatementAPI(file, tableNumber) {
        const formData = new FormData();
        formData.append('pdf_file', file);

        try {
            const response = await fetch('https://openmca.com/ending-balances/extract', {
                method: 'POST',
                body: formData,
                headers: {
                    'Accept': 'application/json',
                },
                mode: 'cors',
                credentials: 'omit'
            });

            if (!response.ok) {
                throw new Error(`API request failed: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();
            
            // Transform API response to match our expected format
            return {
                balances: data.balances.map(item => ({
                    date: item.date,
                    balance: item.ending_balance.toFixed(2)
                })),
                bankLogo: data.bank ? `https://openmca.com${data.bank}` : null
            };
        } catch (error) {
            console.error('API Error:', error);
            throw new Error(`Failed to process statement: ${error.message}`);
        }
    }

    generateSampleData() {
        const data = [];
        const startDate = new Date('2024-01-01');
        const numEntries = 10 + Math.floor(Math.random() * 20);
        let balance = 5000 + Math.random() * 10000;

        for (let i = 0; i < numEntries; i++) {
            const date = new Date(startDate);
            date.setDate(date.getDate() + i);
            
            // Random daily change
            const change = (Math.random() - 0.3) * 1000;
            balance += change;
            
            data.push({
                date: date.toLocaleDateString('en-US', { 
                    month: 'short', 
                    day: '2-digit',
                    year: 'numeric'
                }),
                balance: balance.toFixed(2)
            });
        }

        return data;
    }

    populateTable(tableNumber, data, fileName) {
        const tbody = document.getElementById(`tbody-${tableNumber}`);
        const tableHeader = document.querySelector(`#table-${tableNumber}`).closest('.table-container').querySelector('.table-header h3');
        
        // Clear existing data
        tbody.innerHTML = '';
        
        // Add new rows
        data.balances.forEach((row, index) => {
            const tr = document.createElement('tr');
            const balance = parseFloat(row.balance);
            const balanceClass = balance >= 0 ? 'balance-positive' : 'balance-negative';
            
            tr.innerHTML = `
                <td>${row.date}</td>
                <td class="${balanceClass}">$${Math.abs(balance).toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
            `;
            
            // Add animation
            tr.style.opacity = '0';
            tr.style.transform = 'translateY(20px)';
            
            tbody.appendChild(tr);
            
            // Animate in
            setTimeout(() => {
                tr.style.transition = 'all 0.3s ease';
                tr.style.opacity = '1';
                tr.style.transform = 'translateY(0)';
            }, index * 50);
        });

        // Update table header with bank logo if available
        if (data.bankLogo) {
            tableHeader.innerHTML = `
                <div class="table-title-with-logo">
                    <img src="${data.bankLogo}" alt="Bank Logo" class="bank-logo" onerror="this.style.display='none'">
                </div>
            `;
        }
        // Store data
        this.tables.set(tableNumber, { data, fileName });
        this.updateDropZoneState();
    }

    clearTable(tableNumber) {
        const tbody = document.getElementById(`tbody-${tableNumber}`);
        const tableHeader = document.querySelector(`#table-${tableNumber}`).closest('.table-container').querySelector('.table-header h3');
        
        // Reset table
        tbody.innerHTML = '<tr class="empty-row"><td colspan="2">No data available</td></tr>';
        
        // Reset table header to show icon
        tableHeader.innerHTML = `
            <svg class="table-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                <line x1="9" y1="9" x2="15" y2="9"/>
                <line x1="9" y1="15" x2="15" y2="15"/>
            </svg>
        `;
        
        // Remove from storage
        this.tables.delete(tableNumber);
        
        // Update status
        this.updateTableStatus(tableNumber, 'empty');
        this.updateDropZoneState();

        // Add animation
        const emptyRow = tbody.querySelector('.empty-row');
        emptyRow.style.opacity = '0';
        setTimeout(() => {
            emptyRow.style.transition = 'opacity 0.3s ease';
            emptyRow.style.opacity = '1';
        }, 100);
    }

    clearAllTables() {
        for (let i = 1; i <= this.maxTables; i++) {
            if (this.tables.has(i.toString())) {
                this.clearTable(i.toString());
            }
        }
    }

    showNotification(message, type = 'info') {
        // Simple notification system - you can enhance this
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 1000;
            max-width: 300px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            transition: all 0.3s ease;
        `;
        
        switch (type) {
            case 'error':
                notification.style.backgroundColor = '#ef4444';
                break;
            case 'warning':
                notification.style.backgroundColor = '#f59e0b';
                break;
            case 'success':
                notification.style.backgroundColor = '#10b981';
                break;
            default:
                notification.style.backgroundColor = '#2563eb';
        }
        
        notification.textContent = message;
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        // Remove after 4 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 4000);
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new BankStatementComparison();
});

// Prevent default drag behavior on the entire document
document.addEventListener('dragover', (e) => {
    e.preventDefault();
});

document.addEventListener('drop', (e) => {
    e.preventDefault();
});