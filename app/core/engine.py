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

def generate_stealth(hostname, mode="aggressive"):
    var_mat = obfuscate_variable()
    var_det = obfuscate_variable()
    var_poison1 = obfuscate_variable()
    var_poison2 = obfuscate_variable()
    var_combo = obfuscate_variable()
    var_density = obfuscate_variable()
    var_offset = obfuscate_variable()

    var_processed = obfuscate_variable()
    var_observer = obfuscate_variable()

    js_code = rf"""(function(){{
        const _auth = atob("{base64.b64encode(hostname.encode()).decode()}");
        if (window.location.hostname !== _auth && window.location.hostname !== "127.0.0.1" && window.location.hostname !== "localhost") return;

        const pool = [8204, 8205, 8288]; 
        const {var_mat} = [[Math.floor(Math.random()*10),3,5],[2,Math.floor(Math.random()*10),8],[1,4,Math.floor(Math.random()*10)]];
        function getDet(m) {{
            return m[0][0]*(m[1][1]*m[2][2]-m[1][2]*m[2][1]) - m[0][1]*(m[1][0]*m[2][2]-m[1][2]*m[2][0]) + m[0][2]*(m[1][0]*m[2][1]-m[1][1]*m[2][0]);
        }}
        const {var_det} = Math.abs(getDet({var_mat}));
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
                const currentPoison = Math.random() < 0.5 ? {var_poison1} : {var_combo};
                if (!node.nodeValue.includes(currentPoison)) {{
                    const {var_density} = ({var_det} % 4) + 3;
                    const {var_offset} = {var_det} % {var_density};
                    let original = node.nodeValue;
                    let result = "";
                    for (let i = 0; i < original.length; i++) {{
                        result += original[i];
                        if (original[i] !== ' ' && (i + {var_offset}) % {var_density} === 0 && Math.random() < 0.85) {{
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

    return minify_js(js_code)