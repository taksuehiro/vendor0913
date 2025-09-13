async function testCors() {
    const result = document.getElementById('result');
    result.innerHTML = '';
    
    const tests = [
        { method: 'GET', url: 'http://127.0.0.1:8001/cors-test' },
        { method: 'POST', url: 'http://127.0.0.1:8001/cors-test' }
    ];
    
    for (const test of tests) {
        try {
            console.log(`Testing ${test.method} ${test.url}`);
            
            const response = await fetch(test.url, {
                method: test.method,
                headers: { 'Content-Type': 'application/json' }
            });
            
            const data = await response.json();
            result.innerHTML += `<p style="color:green">${test.method}: SUCCESS - ${JSON.stringify(data)}</p>`;
            
        } catch (error) {
            result.innerHTML += `<p style="color:red">${test.method}: FAILED - ${error.message}</p>`;
            console.error(`${test.method} failed:`, error);
        }
    }
}

