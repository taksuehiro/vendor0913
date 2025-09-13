async function debugLogin() {
    console.clear();
    console.log('=== Starting debug login test ===');
    
    const testData = {
        email: 'test@example.com',
        password: 'password123'
    };
    
    console.log('Test data:', testData);
    console.log('JSON string:', JSON.stringify(testData));
    console.log('JSON string length:', JSON.stringify(testData).length);
    
    try {
        const response = await fetch('http://127.0.0.1:8003/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(testData)
        });
        
        console.log('Response received');
        console.log('Status:', response.status);
        console.log('Status text:', response.statusText);
        console.log('Headers:', Object.fromEntries(response.headers.entries()));
        
        const responseText = await response.text();
        console.log('Response text:', responseText);
        
        if (response.ok) {
            const data = JSON.parse(responseText);
            console.log('Parsed response:', data);
            document.getElementById('result').innerHTML = 
                `<div class="success">SUCCESS: ${JSON.stringify(data, null, 2)}</div>`;
        } else {
            console.error('Request failed with status:', response.status);
            document.getElementById('result').innerHTML = 
                `<div class="error">FAILED (${response.status}): ${responseText}</div>`;
        }
        
    } catch (error) {
        console.error('Network error:', error);
        document.getElementById('result').innerHTML = 
            `<div class="error">NETWORK ERROR: ${error.message}</div>`;
    }
}

