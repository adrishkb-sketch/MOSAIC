import json
import subprocess
import os
import base64
from typing import Dict, Any, Optional

class WebcmdClient:
    def _get_env(self) -> Dict[str, str]:
        env = os.environ.copy()
        # Prepend standard Homebrew/Mac paths to PATH to ensure Homebrew Node is used
        paths = ["/opt/homebrew/bin", "/usr/local/bin", "/usr/bin", "/bin"]
        existing_path = env.get("PATH", "")
        if existing_path:
            env["PATH"] = os.pathsep.join(paths) + os.pathsep + existing_path
        else:
            env["PATH"] = os.pathsep.join(paths)
            
        # Add Node module resolution paths
        global_node_paths = [
            "/opt/homebrew/lib/node_modules",
            "/usr/local/lib/node_modules",
            os.path.expanduser("~/.npm-global/lib/node_modules")
        ]
        existing_node_path = env.get("NODE_PATH", "")
        if existing_node_path:
            env["NODE_PATH"] = existing_node_path + os.pathsep + os.pathsep.join(global_node_paths)
        else:
            env["NODE_PATH"] = os.pathsep.join(global_node_paths)
            
        return env

    def create_session(self) -> str:
        """
        Creates a new Webcmd session and returns the opaque session ID.
        """
        try:
            result = subprocess.run(
                ["webcmd", "session", "create", "-f", "json"],
                capture_output=True,
                text=True,
                check=True,
                env=self._get_env()
            )
            data = json.loads(result.stdout)
            return data["id"]
        except Exception as e:
            raise RuntimeError(f"Failed to create Webcmd session: {str(e)}")

    def close_session(self, session_id: str) -> None:
        """
        Closes the browser session.
        """
        try:
            subprocess.run(
                ["webcmd", "--session", session_id, "browser", "close"],
                capture_output=True,
                text=True,
                check=True,
                env=self._get_env()
            )
        except Exception as e:
            # We don't want to crash if closing fails (session might be already closed)
            print(f"Warning: Failed to close Webcmd session {session_id}: {e}")

    def run_script(self, session_id: str, script: str, timeout: int = 15) -> Dict[str, Any]:
        """
        Runs a Playwright JavaScript snippet in the session.
        """
        try:
            # Increase output limit to 10MB to accommodate rich DOM evaluations
            process = subprocess.Popen(
                ["webcmd", "--session", session_id, "browser", "run", "--stdin", "--max-output", "10000000", "--timeout", str(timeout)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=self._get_env()
            )
            stdout, stderr = process.communicate(input=script)
            
            if process.returncode != 0:
                raise RuntimeError(f"Webcmd run failed (code {process.returncode}): {stderr or stdout}")
            
            try:
                return json.loads(stdout)
            except json.JSONDecodeError:
                raise RuntimeError(f"Failed to parse Webcmd output as JSON: {stdout}")
                
        except Exception as e:
            raise RuntimeError(f"Error executing script in Webcmd: {str(e)}")

    def scroll_page(self, session_id: str, direction: str = "down", amount: int = 600) -> bool:
        """Scrolls the live browser page up or down."""
        delta = amount if direction == "down" else -amount
        script = f"""
        window.scrollBy({{ top: {delta}, behavior: 'smooth' }});
        return true;
        """
        try:
            res = self.run_script(session_id, script, timeout=5)
            return bool(res.get("ok"))
        except Exception:
            return False

    def get_screenshot(self, session_id: str) -> Optional[str]:
        """
        Captures a base64 PNG screenshot of the active browser page.
        Returns a data URL: 'data:image/png;base64,...'
        """
        script = "const buffer = await page.screenshot(); return buffer.toString('base64');"
        try:
            res = self.run_script(session_id, script, timeout=12)
            if not res.get("ok") or not res.get("result"):
                return None
                
            raw_result = res["result"]
            
            # If the result is a comma-separated list of bytes
            if isinstance(raw_result, str) and "," in raw_result:
                try:
                    byte_values = [int(x.strip()) for x in raw_result.split(",") if x.strip()]
                    byte_data = bytes(byte_values)
                    b64_data = base64.b64encode(byte_data).decode("utf-8")
                    return f"data:image/png;base64,{b64_data}"
                except Exception:
                    pass
            
            # If it's a dict mapping indexes to bytes
            if isinstance(raw_result, dict):
                try:
                    sorted_keys = sorted([int(k) for k in raw_result.keys()])
                    byte_values = [raw_result[str(k)] for k in sorted_keys]
                    byte_data = bytes(byte_values)
                    b64_data = base64.b64encode(byte_data).decode("utf-8")
                    return f"data:image/png;base64,{b64_data}"
                except Exception:
                    pass

            # Fallback if it is already a base64 string
            if isinstance(raw_result, str):
                clean_str = raw_result.strip()
                if clean_str.startswith("data:image"):
                    return clean_str
                return f"data:image/png;base64,{clean_str}"
                
            return None
        except Exception as e:
            print(f"Warning: Failed to capture screenshot: {e}")
            return None




    def get_accessibility_snapshot(self, session_id: str) -> str:
        """
        Returns the compact accessibility snapshot (ACT tree) for Gemini reasoning.
        """
        try:
            result = subprocess.run(
                ["webcmd", "--session", session_id, "browser", "snapshot", "--snapshot-mode", "act"],
                capture_output=True,
                text=True,
                check=True,
                env=self._get_env()
            )
            return result.stdout.strip()
        except Exception as e:
            print(f"Warning: Failed to capture page snapshot: {e}")
            return "Unable to capture website accessibility tree."

    def dismiss_cookie_and_popups(self, session_id: str) -> None:
        """Dismisses common cookie banners or popups."""
        script = """
        await page.evaluate(() => {
            const buttons = Array.from(document.querySelectorAll('button, a, div[role="button"]'));
            for (const b of buttons) {
                const txt = (b.innerText || b.textContent || "").trim().toLowerCase();
                if (txt === 'accept all' || txt === 'i agree' || txt === 'agree' || txt === 'accept cookies' || txt === 'got it' || txt === 'continue' || txt === 'close') {
                    if (b.offsetParent !== null) { // visible
                        b.click();
                        break;
                    }
                }
            }
        });
        """
        try:
            self.run_script(session_id, script, timeout=5)
        except Exception:
            pass

    def navigate_to(self, session_id: str, url: str) -> Dict[str, Any]:
        """Navigates to URL and waits for page load."""
        script = f"""
        await page.goto("{url}", {{ waitUntil: 'domcontentloaded', timeout: 15000 }});
        await page.waitForTimeout(1500);
        """
        res = self.run_script(session_id, script, timeout=20)
        self.dismiss_cookie_and_popups(session_id)
        return res

    def extract_page_details(self, session_id: str) -> Dict[str, Any]:
        """
        Extracts structured semantic information from the active webpage,
        including URL, title, detected page category, product cards/options,
        input fields, and primary action buttons.
        """
        script = """
        return await page.evaluate(() => {
            const url = window.location.href;
            const title = document.title;
            const bodyText = document.body ? document.body.innerText.slice(0, 5000) : "";
            const lowerBody = bodyText.toLowerCase();

            // Detect page category
            let is_payment_screen = lowerBody.includes("payment method") || lowerBody.includes("select a payment") || lowerBody.includes("upi") || lowerBody.includes("credit card") || lowerBody.includes("cvv") || lowerBody.includes("place your order") || lowerBody.includes("review order");
            let is_otp_screen = lowerBody.includes("enter otp") || lowerBody.includes("verification code") || lowerBody.includes("one time password") || lowerBody.includes("security code") || lowerBody.includes("check your phone") || lowerBody.includes("check your email");
            let is_login_screen = lowerBody.includes("sign-in") || lowerBody.includes("sign in") || lowerBody.includes("log in") || lowerBody.includes("login") || lowerBody.includes("password") || lowerBody.includes("create account");
            let is_shipping_screen = lowerBody.includes("shipping address") || lowerBody.includes("delivery address") || lowerBody.includes("pin code") || lowerBody.includes("pincode") || lowerBody.includes("postal code") || lowerBody.includes("address line");

            // Extract visible items / products if on search or catalog page
            const items = [];
            // Comprehensive modern selectors for Flipkart, Amazon, and generic e-commerce
            const productNodes = document.querySelectorAll(
                '[data-id], .tUxRFH, .cPHDOP, ._75nlfW, ._1AtVbE, ._2kHMtA, ._4ddWXP, ._1xHGtK, [data-component-type="s-search-result"], .s-result-item, .product-card, article, [data-asin]'
            );
            
            for (const node of productNodes) {
                if (items.length >= 6) break;
                // Try multiple title selectors across different portal designs
                const titleEl = node.querySelector(
                    '.KzDlHZ, ._4rR01Z, .s1Q9rs, .wjcEIp, ._2WkVRV, .IRpwTa, .DByuf4, h2 a, h3 a, h2 span, .a-text-normal, a.title, .product-title, h2, h3, [title]'
                );
                // Try multiple price selectors
                const priceEl = node.querySelector(
                    '.Nx9q9m, ._30jeq3, .hl05eU, ._25b18c, .a-price .a-offscreen, .a-price-whole, .price, .product-price, [data-price]'
                );
                // Try to find direct link
                const linkEl = node.querySelector(
                    'a.CGtC58, a.VJA3rP, a._1fQZEK, h2 a, h3 a, a[href*="/p/"], a[href*="/dp/"], a[href*="/itm/"], a[href*="/product/"], a'
                );
                
                let itemTitle = titleEl ? (titleEl.innerText || titleEl.getAttribute('title') || "").trim() : "";
                let itemPrice = priceEl ? (priceEl.innerText || priceEl.textContent || "").trim() : "";
                let itemHref = linkEl ? linkEl.href : "";

                // If no price from priceEl, regex search within node text
                if (!itemPrice) {
                    const nodeTxt = node.innerText || "";
                    const m = nodeTxt.match(/(?:₹|Rs\.?|\$)\s*[\d,]+(?:\.\d+)?/);
                    if (m) itemPrice = m[0];
                }

                if (itemTitle && itemTitle.length > 3 && !items.some(i => i.title === itemTitle)) {
                    // Clean up title
                    itemTitle = itemTitle.split('\n')[0].trim();
                    items.push({
                        title: itemTitle.slice(0, 100),
                        price: itemPrice || "Check Price",
                        url: itemHref,
                        selector: linkEl ? `a[href="${linkEl.getAttribute('href')}"]` : null
                    });
                }
            }

            // Fallback: if no items found, scan links containing prices
            if (items.length === 0) {
                const links = Array.from(document.querySelectorAll('a'));
                for (const l of links) {
                    if (items.length >= 6) break;
                    const txt = l.innerText ? l.innerText.trim() : "";
                    const priceMatch = txt.match(/(?:₹|Rs\.?|\$)\s*[\d,]+(?:\.\d+)?/);
                    if (priceMatch && txt.length > 10 && !txt.toLowerCase().includes("cart") && !txt.toLowerCase().includes("login")) {
                        const lines = txt.split('\n').map(s => s.trim()).filter(Boolean);
                        const title = lines.find(line => !line.match(/(?:₹|Rs\.?|\$)/) && line.length > 5) || lines[0];
                        if (title && !items.some(i => i.title === title)) {
                            items.push({
                                title: title.slice(0, 100),
                                price: priceMatch[0],
                                url: l.href,
                                selector: `a[href="${l.getAttribute('href')}"]`
                            });
                        }
                    }
                }
            }


            // Extract visible input fields
            const inputs = [];
            const inputNodes = document.querySelectorAll('input, textarea, select');
            for (const inp of inputNodes) {
                if (inp.type === 'hidden') continue;
                const id = inp.id || "";
                const name = inp.name || "";
                const placeholder = inp.placeholder || "";
                const type = inp.type || "text";
                const labelEl = id ? document.querySelector(`label[for="${id}"]`) : null;
                const label = labelEl ? labelEl.innerText.trim() : "";
                
                let selector = "";
                if (id) selector = `#${id}`;
                else if (name) selector = `[name="${name}"]`;
                else if (placeholder) selector = `[placeholder="${placeholder}"]`;

                if (selector) {
                    inputs.push({ id, name, placeholder, label, type, selector });
                }
            }

            // Extract visible action buttons
            const buttons = [];
            const buttonNodes = document.querySelectorAll('button, input[type="submit"], input[type="button"], a.btn, a[role="button"], #buy-now-button, #add-to-cart-button');
            for (const btn of buttonNodes) {
                if (buttons.length >= 10) break;
                const btnText = (btn.innerText || btn.value || "").trim();
                const id = btn.id || "";
                const name = btn.name || "";
                let selector = "";
                if (id) selector = `#${id}`;
                else if (name) selector = `[name="${name}"]`;
                else if (btn.className) selector = `.${btn.className.split(' ').filter(c => c).join('.')}`;

                if (btnText && btnText.length < 50) {
                    buttons.push({ text: btnText, selector: selector || null });
                }
            }

            let page_type = "general";
            if (is_payment_screen) page_type = "checkout_payment";
            else if (is_otp_screen) page_type = "auth_otp";
            else if (is_login_screen) page_type = "auth_login";
            else if (is_shipping_screen) page_type = "shipping_address";
            else if (items.length > 0) page_type = "search_results";

            return {
                url,
                title,
                page_type,
                items,
                inputs,
                buttons,
                is_payment_screen,
                is_otp_screen,
                is_login_screen,
                is_shipping_screen
            };
        });
        """
        try:
            res = self.run_script(session_id, script, timeout=10)
            if res.get("ok") and isinstance(res.get("result"), dict):
                return res["result"]
            return {"url": "", "title": "", "page_type": "general", "items": [], "inputs": [], "buttons": []}
        except Exception as e:
            print(f"Warning: extract_page_details failed: {e}")
            return {"url": "", "title": "", "page_type": "general", "items": [], "inputs": [], "buttons": []}

    def press_key(self, session_id: str, key: str = "Enter") -> bool:
        """Presses a keyboard key such as 'Enter' or 'Tab'."""
        script = f"""
        await page.keyboard.press("{key}");
        return true;
        """
        try:
            res = self.run_script(session_id, script, timeout=5)
            return bool(res.get("ok") and res.get("result"))
        except Exception:
            return False

    def click_element(self, session_id: str, selector: Optional[str] = None, text: Optional[str] = None) -> bool:
        """Clicks an element by CSS selector or visible text."""
        script = f"""
        await page.evaluate(() => {{
            const targetSelector = {json.dumps(selector)};
            const targetText = {json.dumps(text.lower() if text else None)};
            
            if (targetSelector) {{
                try {{
                    const el = document.querySelector(targetSelector);
                    if (el) {{
                        el.scrollIntoView({{ behavior: 'instant', block: 'center' }});
                        el.click();
                        return true;
                    }}
                }} catch (e) {{}}
            }}
            
            if (targetText) {{
                const all = Array.from(document.querySelectorAll('button, a, input[type="button"], input[type="submit"], div[role="button"], span, div, li'));
                for (const el of all) {{
                    const t = (el.innerText || el.value || el.textContent || "").trim().toLowerCase();
                    if (t === targetText || (t.includes(targetText) && t.length < targetText.length + 25)) {{
                        el.scrollIntoView({{ behavior: 'instant', block: 'center' }});
                        el.click();
                        return true;
                    }}
                }}
            }}
            return false;
        }});
        """
        try:
            res = self.run_script(session_id, script, timeout=10)
            return bool(res.get("ok") and res.get("result"))
        except Exception:
            return False

    def fill_element(self, session_id: str, selector: str, value: str, press_enter: bool = False) -> bool:
        """Fills value into an input field and optionally presses Enter."""
        script = f"""
        await page.evaluate(() => {{
            const sel = {json.dumps(selector)};
            const val = {json.dumps(value)};
            const el = document.querySelector(sel);
            if (el) {{
                el.scrollIntoView({{ behavior: 'instant', block: 'center' }});
                el.focus();
                el.value = val;
                el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                return true;
            }}
            return false;
        }});
        """
        try:
            res = self.run_script(session_id, script, timeout=10)
            if press_enter and res.get("ok") and res.get("result"):
                self.press_key(session_id, "Enter")
            return bool(res.get("ok") and res.get("result"))
        except Exception:
            return False

webcmd_client = WebcmdClient()


