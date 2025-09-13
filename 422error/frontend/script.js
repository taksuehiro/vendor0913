async function testLogin() {
    const resultDiv = document.getElementById('result');
    resultDiv.innerHTML = 'Sending request...';
    
    try {
        console.log('Sending login request...');
        
        const requestData = {
            email: 'test@example.com',
            password: 'password'
        };
        
        console.log('Request data:', requestData);
        
        const response = await fetch('http://localhost:8001/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });
        
        console.log('Response status:', response.status);
        console.log('Response headers:', [...response.headers.entries()]);
        
        if (!response.ok) {
            const errorData = await response.text();
            console.error('Error response:', errorData);
            resultDiv.innerHTML = `
                <div style="color: red;">
                    <h3>Error ${response.status}: ${response.statusText}</h3>
                    <pre>${errorData}</pre>
                </div>
            `;
            return;
        }
        
        const data = await response.json();
        console.log('Success data:', data);
        resultDiv.innerHTML = `
            <div style="color: green;">
                <h3>Success!</h3>
                <pre>${JSON.stringify(data, null, 2)}</pre>
            </div>
        `;
    } catch (error) {
        console.error('Network error:', error);
        resultDiv.innerHTML = `
            <div style="color: red;">
                <h3>Network Error:</h3>
                <p>${error.message}</p>
            </div>
        `;
    }
}

// ヘルスチェック機能追加
async function checkHealth() {
    try {
        const response = await fetch('http://localhost:8001/health');
        const data = await response.json();
        console.log('Health check:', data);
        document.getElementById('result').innerHTML = `
            <div style="color: blue;">
                <h3>Health Check:</h3>
                <pre>${JSON.stringify(data, null, 2)}</pre>
            </div>
        `;
    } catch (error) {
        document.getElementById('result').innerHTML = `
            <div style="color: red;">
                <h3>Health Check Failed:</h3>
                <p>${error.message}</p>
            </div>
        `;
    }
}