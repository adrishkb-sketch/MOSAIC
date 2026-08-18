import json
import subprocess
import os
import base64
from typing import Dict, Any, Optional

class WebcmdClient:
    def create_session(self) -> str:
        """
        Creates a new Webcmd session and returns the opaque session ID.
        """
        try:
            result = subprocess.run(
                ["webcmd", "session", "create", "-f", "json"],
                capture_output=True,
                text=True,
                check=True
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
                check=True
            )
        except Exception as e:
            # We don't want to crash if closing fails (session might be already closed)
            print(f"Warning: Failed to close Webcmd session {session_id}: {e}")

    def run_script(self, session_id: str, script: str, timeout: int = 15) -> Dict[str, Any]:
        """
        Runs a Playwright JavaScript snippet in the session.
        """
        try:
            # We use subprocess.Popen to pipe the script to stdin
            process = subprocess.Popen(
                ["webcmd", "--session", session_id, "browser", "run", "--stdin", "--max-output", "2000000", "--timeout", str(timeout)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
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

    def get_screenshot(self, session_id: str) -> Optional[str]:
        """
        Captures a base64 screenshot of the active browser page.
        Returns a data URL: 'data:image/png;base64,...'
        """
        script = "const buffer = await page.screenshot(); return buffer.toString();"
        try:
            res = self.run_script(session_id, script)
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
                    # Sort keys to preserve order
                    sorted_keys = sorted([int(k) for k in raw_result.keys()])
                    byte_values = [raw_result[str(k)] for k in sorted_keys]
                    byte_data = bytes(byte_values)
                    b64_data = base64.b64encode(byte_data).decode("utf-8")
                    return f"data:image/png;base64,{b64_data}"
                except Exception:
                    pass

            # Fallback if it is already a base64 string
            if isinstance(raw_result, str):
                # Check if it contains commas or is pure base64
                if raw_result.startswith("iVBORw"):  # Standard PNG base64 header
                    return f"data:image/png;base64,{raw_result}"
                else:
                    # Try to see if it is a byte string representation
                    clean_str = raw_result.strip()
                    # If it's pure base64
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
                check=True
            )
            # Remove any terminal colors or headers
            return result.stdout.strip()
        except Exception as e:
            print(f"Warning: Failed to capture page snapshot: {e}")
            return "Unable to capture website accessibility tree."

webcmd_client = WebcmdClient()
