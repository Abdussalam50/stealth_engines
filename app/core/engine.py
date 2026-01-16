import base64
import random
import string
import re

def obfuscate_variable(length=8):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

def minify_js(js):
    js = re.sub(r'//.*', '', js)  # Hapus comment
    js = re.sub(r'\s+', ' ', js)  # Collapse whitespace
    return js.strip()

def generate_stealth(hostname, mode='tactical'):
    var_mat = obfuscate_variable()
    var_det = obfuscate_variable()
    var_poison1 = obfuscate_variable()
    var_poison2 = obfuscate_variable()
    var_combo = obfuscate_variable()
    var_density = obfuscate_variable()
    var_offset = obfuscate_variable()

    var_processed = obfuscate_variable()
    var_observer = obfuscate_variable()

    
    # Common variables
    var_processed = obfuscate_variable()
    var_observer = obfuscate_variable()
    
    # RECON mode (Basic)
    if mode == 'recon':
        # Simple static poisoning, low intensity
        var_poison_char = obfuscate_variable()
        
        js_code = rf"""(function(){{
            const _auth = atob("{base64.b64encode(hostname.encode()).decode()}");
            if (window.location.hostname !== _auth && window.location.hostname !== "127.0.0.1" && window.location.hostname !== "localhost") return;

            const {var_poison_char} = String.fromCharCode(8204); // Zero Width Non-Joiner
            const {var_processed} = new WeakSet();

            const processNode = (node) => {{
                if (!node || {var_processed}.has(node)) return;
                
                if (node.nodeType === 1) {{
                    if (['SCRIPT','STYLE','TEXTAREA','INPUT','NOSCRIPT','BUTTON','A','PRE','CODE'].includes(node.tagName)) return;
                    {var_processed}.add(node);
                    node.childNodes.forEach(processNode);
                }} else if (node.nodeType === 3 && node.nodeValue.trim()) {{
                     // Low intensity: 30% chance, static character
                    if (!node.nodeValue.includes({var_poison_char}) && Math.random() < 0.3) {{
                        let original = node.nodeValue;
                        let result = "";
                        for (let i = 0; i < original.length; i++) {{
                            result += original[i];
                            // Insert poison every ~10 chars with some randomness
                            if ((i % 10 === 0) && Math.random() < 0.3) {{
                                result += {var_poison_char};
                            }}
                        }}
                        node.nodeValue = result;
                    }}
                    {var_processed}.add(node);
                }}
            }};

            window.activateStealth = function() {{
                if (document.body) processNode(document.body);
            }};
            
             if (document.body) {{
                window.activateStealth();
            }} else {{
                document.addEventListener('DOMContentLoaded', () => {{
                    window.activateStealth();
                }});
            }}
        }})();"""

    # TACTICAL mode (Advanced) - Existing Logic + Bot Detection
    elif mode == 'tactical':
        var_mat = obfuscate_variable()
        var_det = obfuscate_variable()
        var_poison1 = obfuscate_variable()
        var_poison2 = obfuscate_variable()
        var_combo = obfuscate_variable()
        var_density = obfuscate_variable()
        var_offset = obfuscate_variable()
        var_bot_detect = obfuscate_variable()

        js_code = rf"""(function(){{
            const _auth = atob("{base64.b64encode(hostname.encode()).decode()}");
            if (window.location.hostname !== _auth && window.location.hostname !== "127.0.0.1" && window.location.hostname !== "localhost") return;

            const pool = [8204, 8205, 8288]; 
            // Dynamic Matrix Calculation
            const {var_mat} = [[Math.floor(Math.random()*10),3,5],[2,Math.floor(Math.random()*10),8],[1,4,Math.floor(Math.random()*10)]];
            function getDet(m) {{
                return m[0][0]*(m[1][1]*m[2][2]-m[1][2]*m[2][1]) - m[0][1]*(m[1][0]*m[2][2]-m[1][2]*m[2][0]) + m[0][2]*(m[1][0]*m[2][1]-m[1][1]*m[2][0]);
            }}
            const {var_det} = Math.abs(getDet({var_mat}));
            const {var_poison1} = String.fromCharCode(pool[{var_det} % pool.length]);
            const {var_poison2} = String.fromCharCode(pool[({var_det} + 1) % pool.length]);
            const {var_combo} = {var_poison1} + {var_poison2};
            const {var_processed} = new WeakSet();

            // Simple Bot Detection (User-Agent or WebDriver)
            let isBot = false;
            if (navigator.webdriver || /HeadlessChrome/.test(navigator.userAgent)) {{
                isBot = true;
            }}

            const processNode = (node) => {{
                if (!node || {var_processed}.has(node)) return;
                
                if (node.nodeType === 1) {{
                    if (['SCRIPT','STYLE','TEXTAREA','INPUT','NOSCRIPT','BUTTON','A','PRE','CODE'].includes(node.tagName)) return;
                    {var_processed}.add(node);
                    node.childNodes.forEach(processNode);
                }} else if (node.nodeType === 3 && node.nodeValue.trim()) {{
                    const currentPoison = Math.random() < 0.5 ? {var_poison1} : {var_combo};
                    if (!node.nodeValue.includes(currentPoison)) {{
                        // Super Poisoning if Bot Detected
                        const baseDensity = isBot ? 2 : 4; 
                        const {var_density} = ({var_det} % baseDensity) + (isBot ? 1 : 3);
                        const {var_offset} = {var_det} % {var_density};
                        let original = node.nodeValue;
                        let result = "";
                        for (let i = 0; i < original.length; i++) {{
                            result += original[i];
                            if (original[i] !== ' ' && (i + {var_offset}) % {var_density} === 0 && Math.random() < (isBot ? 0.99 : 0.85)) {{
                                result += Math.random() < 0.6 ? currentPoison : {var_poison2};
                            }}
                        }}
                        node.nodeValue = result;
                    }}
                    {var_processed}.add(node);
                }}
            }};

            window.activateStealth = function() {{
                if (document.body) processNode(document.body);
            }};

            const {var_observer} = new MutationObserver((mutations) => {{
                mutations.forEach(m => {{
                    m.addedNodes.forEach(processNode);
                }});
            }});

            if (document.body) {{
                window.activateStealth();
                {var_observer}.observe(document.body, {{ childList: true, subtree: true }});
            }} else {{
                document.addEventListener('DOMContentLoaded', () => {{
                    window.activateStealth();
                    {var_observer}.observe(document.body, {{ childList: true, subtree: true }});
                }});
            }}
        }})();"""

    # SOVEREIGN mode (Elite) - Honey Pots, Self-Destruct, stricter checks
    else: # sovereign
        var_mat = obfuscate_variable()
        var_det = obfuscate_variable()
        var_poison1 = obfuscate_variable()
        var_poison2 = obfuscate_variable()
        var_combo = obfuscate_variable() 
        var_honey = obfuscate_variable()
        var_check = obfuscate_variable()
        
        # Honey pot content - invisible data
        honey_pot_html = f'<div style="opacity:0.001;position:absolute;left:-9999px;top:0;">Price: Rp 0<br>Stock: 99999<br>Discount: 100%</div>'
        
        js_code = rf"""(function(){{
            const _auth = atob("{base64.b64encode(hostname.encode()).decode()}");
            
            // Self-Destruct / Strict Check
            function {var_check}() {{
                if (window.location.hostname !== _auth && window.location.hostname !== "127.0.0.1" && window.location.hostname !== "localhost") {{
                    // Silent fail or annoy
                    document.body.innerHTML = '<h1>Error 500: Internal Server Error</h1>';
                    throw new Error("System Failure");
                }}
            }}
            {var_check}();

            const pool = [8204, 8205, 8288, 8290, 8291]; // Extended pool for Elite
            const {var_mat} = [[Math.floor(Math.random()*10),3,5],[2,Math.floor(Math.random()*10),8],[1,4,Math.floor(Math.random()*10)]];
            const {var_det} = Math.abs((m => m[0][0]*(m[1][1]*m[2][2]-m[1][2]*m[2][1]) - m[0][1]*(m[1][0]*m[2][2]-m[1][2]*m[2][0]) + m[0][2]*(m[1][0]*m[2][1]-m[1][1]*m[2][0]))({var_mat}));
            
            const {var_poison1} = String.fromCharCode(pool[{var_det} % pool.length]);
            const {var_poison2} = String.fromCharCode(pool[({var_det} + 1) % pool.length]);
            const {var_combo} = {var_poison1} + {var_poison2};
            const {var_processed} = new WeakSet();

            const processNode = (node) => {{
                if (!node || {var_processed}.has(node)) return;
                
                if (node.nodeType === 1) {{
                     if (['SCRIPT','STYLE','TEXTAREA','INPUT','NOSCRIPT','BUTTON','A','PRE','CODE'].includes(node.tagName)) return;
                    {var_processed}.add(node);
                    node.childNodes.forEach(processNode);
                }} else if (node.nodeType === 3 && node.nodeValue.trim()) {{
                    // High density poisoning
                    const currentPoison = Math.random() < 0.5 ? {var_poison1} : {var_combo};
                     if (!node.nodeValue.includes(currentPoison)) {{
                        let original = node.nodeValue;
                        let result = "";
                        let density = 3; 
                        for (let i = 0; i < original.length; i++) {{
                            result += original[i];
                            if (original[i] !== ' ' && (i % density === 0)) {{
                                result += Math.random() < 0.7 ? currentPoison : {var_poison2};
                            }}
                        }}
                        node.nodeValue = result;
                    }}
                    {var_processed}.add(node);
                }}
            }};

            // Honey Pot Injection
            function {var_honey}() {{
                const d = document.createElement('div');
                d.innerHTML = '{honey_pot_html}';
                document.body.appendChild(d);
            }}

            window.activateStealth = function() {{
                {var_check}();
                if (document.body) {{
                    processNode(document.body);
                    {var_honey}();
                }}
            }};

            const {var_observer} = new MutationObserver((mutations) => {{
                mutations.forEach(m => {{
                    m.addedNodes.forEach(processNode);
                }});
            }});

            if (document.body) {{
                window.activateStealth();
                {var_observer}.observe(document.body, {{ childList: true, subtree: true }});
            }} else {{
                document.addEventListener('DOMContentLoaded', () => {{
                    window.activateStealth();
                    {var_observer}.observe(document.body, {{ childList: true, subtree: true }});
                }});
            }}
        }})();"""

    return minify_js(js_code)