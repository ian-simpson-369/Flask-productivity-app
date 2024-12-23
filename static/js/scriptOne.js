
        // Stopwatch functionality
        class Stopwatch {
            constructor(element, targetTime) {
                this.element = element;
                this.targetTime = targetTime;
                this.timerDisplay = this.element.querySelector('.timer');
                this.startBtn = this.element.querySelector('.start-btn');
                this.stopBtn = this.element.querySelector('.stop-btn');
                this.running = false;
                this.startTime = 0;
                this.elapsed = 0;
        
                console.log('Setting up event listeners for:', this.element.id);
                console.log('Timer display:', this.timerDisplay);
                console.log('Start button:', this.startBtn);
                console.log('Stop button:', this.stopBtn);
                this.startBtn.addEventListener('click', () => this.start());
                this.stopBtn.addEventListener('click', () => this.stop());
            }
        
            start() {
                if (!this.running) {
                    console.log('Starting stopwatch');
                    this.running = true;
                    this.startTime = Date.now() - this.elapsed;
                    this.startBtn.classList.add('hidden');
                    this.stopBtn.classList.remove('hidden');
                    this.tick();
                }
            }
        
            stop() {
                if (this.running) {
                    console.log('Stopping stopwatch');
                    this.running = false;
                    this.elapsed = Date.now() - this.startTime;
                    this.startBtn.classList.remove('hidden');
                    this.stopBtn.classList.add('hidden');
        
                    // Send completion to server
                    const duration = Math.floor(this.elapsed / 60000); // Convert to minutes
                    fetch(`/api/stopwatch/${this.element.id.split('-')[1]}/complete`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ duration }),
                    });
                }
            }
        
            tick() {
                if (this.running) {
                    const elapsed = Date.now() - this.startTime;
                    const hours = Math.floor(elapsed / 3600000);
                    const minutes = Math.floor((elapsed % 3600000) / 60000);
                    const seconds = Math.floor((elapsed % 60000) / 1000);
        
                    this.timerDisplay.textContent = 
                        `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        
                    // Change color based on target completion
                    if (minutes >= this.targetTime) {
                        this.element.classList.add('bg-green-100');
                    }
                    
                    console.log('Ticking...', this.timerDisplay.textContent);
                    requestAnimationFrame(() => this.tick());
                }
            }
        }
        
        // Initialize stopwatches
        document.addEventListener('DOMContentLoaded', () => {
            console.log('Initializing stopwatches!');
            document.querySelectorAll('.stopwatch').forEach(element => {
                const targetTimeElement = element.querySelector('.target-time');
        if (targetTimeElement) {
            const targetTime = parseInt(targetTimeElement.textContent.split(' ')[1]);
            console.log('Creating stopwatch for element:', element.id, 'with target time:', targetTime);
            new Stopwatch(element, targetTime);
        } else {
            console.log('Target time element not found for:', element.id);
        }
            });
        });

        //add button
        document.getElementById('add-stopwatch-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const name = document.getElementById('stopwatch-name').value;
            const targetTime = parseInt(document.getElementById('target-time').value);
        
            const response = await fetch('/api/stopwatch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, target_time: targetTime })
            });
        
            if (response.ok) {
                window.location.reload();
            } else {
                alert('Error adding stopwatch.');
            }
        });
        
        //delete button
        document.querySelectorAll('.delete-btn').forEach((button) => {
            button.addEventListener('click', async (e) => {
                const stopwatchId = e.target.closest('[id^="stopwatch-"]').id.split('-')[1];
        
                const response = await fetch(`/api/stopwatch/${stopwatchId}`, { method: 'DELETE' });
        
                if (response.ok) {
                    window.location.reload();
                } else {
                    alert('Error deleting stopwatch.');
                }
            });
        });
        

        // Load and render stats
        async function loadStats() {
            try {
            const response = await fetch('/api/stats');
            if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Received stats data:', data);

            // Create default data if empty
            const defaultData = {
            weeklyLabels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
            monthlyLabels: ['Month 1', 'Month 2', 'Month 3', 'Month 4'],
            values: [0, 0, 0, 0]
        };

            // Render weekly stats
            const weeklyChart = new Chart(document.getElementById('weekly-stats'), {
                type: 'bar',
                data: {
                    labels: Object.keys(data.weekly).length > 0 ? 
                        Object.keys(data.weekly) : defaultData.weeklyLabels,
                    datasets: [{
                        label: 'Completed Tasks',
                        data: Object.keys(data.weekly).length > 0 ? 
                        Object.values(data.weekly) : defaultData.values,
                        backgroundColor: 'rgba(59, 130, 246, 0.5)'}]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: {stepSize: 1}}
                            }}
            });

            // Render monthly stats
            const monthlyChart = new Chart(document.getElementById('monthly-stats'), {
                type: 'bar',
                data: {
                    labels: Object.keys(data.monthly).length > 0 ? 
                    Object.keys(data.monthly) : defaultData.monthlyLabels,
                    datasets: [{
                        label: 'Completed Tasks',
                        data: Object.keys(data.monthly).length > 0 ? 
                        Object.values(data.monthly) : defaultData.values,
                        backgroundColor: 'rgba(59, 130, 246, 0.5)'}]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: {
                                    stepSize: 1
                                }
                            }
                        }
                    }
            });

        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }

        loadStats();