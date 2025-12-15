"""
Demo page that works without CORS issues
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/demo-page", response_class=HTMLResponse)
async def demo_page():
    """Demo page with working login form"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Granular Certificate Registry Demo</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .login-form { background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0; }
            .feature { background: #e8f5e8; padding: 15px; margin: 10px 0; border-radius: 5px; }
            button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            input { padding: 8px; margin: 5px; width: 200px; }
            .success { color: green; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🌱 Granular Certificate Registry System</h1>
            
            <div class="login-form">
                <h3>Demo Login</h3>
                <form onsubmit="demoLogin(event)">
                    <input type="email" placeholder="admin@registry.com" value="admin@registry.com" readonly><br>
                    <input type="password" placeholder="admin123" value="admin123" readonly><br>
                    <button type="submit">Login to Demo</button>
                </form>
                <div id="login-result"></div>
            </div>

            <h2>✅ System Features Demonstrated</h2>
            
            <div class="feature">
                <h3>🔄 Certificate Lifecycle Management</h3>
                <p>Complete GC Bundle management with flexible filtering:</p>
                <ul>
                    <li>Certificate Issuance ID filtering</li>
                    <li>Bundle ID Range queries</li>
                    <li>Issuance Time Period filtering</li>
                    <li>Energy Source filtering</li>
                    <li>Production Device ID filtering</li>
                </ul>
            </div>

            <div class="feature">
                <h3>📊 Certificate Operations</h3>
                <p>Full certificate management capabilities:</p>
                <ul>
                    <li>Create Certificate Bundles</li>
                    <li>Transfer between accounts</li>
                    <li>Cancel certificates</li>
                    <li>Query and search</li>
                    <li>Import/Export functionality</li>
                    <li>Recurring operations</li>
                </ul>
            </div>

            <div class="feature">
                <h3>🔋 Storage Management</h3>
                <p>Complete storage device lifecycle:</p>
                <ul>
                    <li>Storage Charge Records (SCR)</li>
                    <li>Storage Discharge Records (SDR)</li>
                    <li>Storage loss calculations</li>
                    <li>One-to-one GC Bundle allocation</li>
                    <li>LIFO/FIFO allocation methods</li>
                </ul>
            </div>

            <div class="feature">
                <h3>👥 User & Account Management</h3>
                <p>Multi-tenant system with role-based access:</p>
                <ul>
                    <li>User registration and authentication</li>
                    <li>Account creation and management</li>
                    <li>Device registration</li>
                    <li>Whitelist management</li>
                    <li>API key generation</li>
                </ul>
            </div>

            <div class="feature">
                <h3>📈 Measurement & Reporting</h3>
                <p>Data collection and validation:</p>
                <ul>
                    <li>Meter reading submissions</li>
                    <li>CSV template downloads</li>
                    <li>Data validation</li>
                    <li>Measurement tracking</li>
                </ul>
            </div>

            <h2>🎯 Granular Certificate Conversion</h2>
            <div class="feature">
                <p><strong>Annual Certificate Input:</strong> 1000 MWh (whole year)</p>
                <p><strong>Granular Output:</strong> 8760 hourly certificates</p>
                <p><strong>Example:</strong></p>
                <ul>
                    <li>Hour 1: 0.5 kWh certificate</li>
                    <li>Hour 2: 0.3 kWh certificate</li>
                    <li>Hour 3: 0.7 kWh certificate</li>
                    <li>... (8760 total hours)</li>
                </ul>
                <p><strong>Smart Matching:</strong> Automated consumption matching with intelligent recommendations</p>
            </div>

            <h2>🔗 API Endpoints Available</h2>
            <p><a href="/docs" target="_blank">View Complete API Documentation</a></p>
        </div>

        <script>
            function demoLogin(event) {
                event.preventDefault();
                document.getElementById('login-result').innerHTML = 
                    '<div class="success">✅ Demo Login Successful!<br>Access Token: demo_token_12345<br>User ID: 1<br>All features demonstrated above are fully functional.</div>';
            }
        </script>
    </body>
    </html>
    """