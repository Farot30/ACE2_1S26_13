import axios from 'axios';

async function run() {
    try {
        const res = await axios.post("http://localhost:5000/api/auth/login", {
            email: "admin@parkguard.com",
            password: "admin"
        });
        const token = res.data.data.token;
        console.log("Token obtained");

        const res2 = await axios.post("http://localhost:5000/api/users", {
            name: "pepa-123-samuel",
            rfid_card: "B91E19B4"
        }, {
            headers: { Authorization: `Bearer ${token}` }
        });
        console.log("Create user response:", res2.data);
    } catch (err) {
        console.error("Error:", err.response ? err.response.data : err.message);
    }
}
run();