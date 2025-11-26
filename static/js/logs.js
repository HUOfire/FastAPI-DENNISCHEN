async function logout() {
    try {
            await fetch('/api/logout', {
                    method: 'POST',
                    credentials: 'include'
            });
            window.location.href="/login";
        }
        catch (error) {
            console.error('Logout error:', error);
        }
}

async function seach_logs(){
     const params = new URLSearchParams({
            date: document.getElementById('date').value,
            level: document.getElementById('level').value,
            keyword: document.getElementById('keyword').value
    });
    try {
        const response = await fetch(`/apilog/get_logs?${params}`, {
            method: 'GET',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            },
        });
        const data = await response.json();
        //console.log(data);
        if (data.code === 200) {
            const logs = data.logs;
            const table = document.getElementById('logs-table');
            table.innerHTML = '';
            logs.forEach(log => {
                const row = table.insertRow();
                const datetimeCell = row.insertCell();
                const levelCell = row.insertCell();
                const messageCell = row.insertCell();
                datetimeCell.innerHTML = log.datetime;
                levelCell.innerHTML = log.level;
                messageCell.innerHTML = log.message;
            });
        }
        else {
            console.error('Search logs error:', data.message);
        }
    }
    catch (error) {
        console.error('Search logs error:', error);
    }
}

