import http.server
import socketserver
import json
import os
import sys
import traceback
import urllib.parse
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Get credentials from environment variables
API_USERNAME = os.getenv("NGI_API_USERNAME")
API_PASSWORD = os.getenv("NGI_API_PASSWORD")

# JWT token cache
token_cache = None

def get_auth_token():
    """Get JWT token from the API"""
    global token_cache
    
    if token_cache:
        print("Using cached token")
        return token_cache
    
    if not API_USERNAME or not API_PASSWORD:
        print("ERROR: Missing API credentials in .env file")
        raise ValueError("Missing API credentials. Check your .env file.")
        
    auth_url = 'https://api.ngidata.com/auth'
    print(f"Authenticating with {auth_url}")
    print(f"Using username: {API_USERNAME}")
    
    try:
        print("Sending authentication request...")
        response = requests.post(
            auth_url,
            json={"email": API_USERNAME, "password": API_PASSWORD},
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()
        
        print(f"Auth response status: {response.status_code}")
        print(f"Auth response data (first 100 chars): {response.text[:100]}")
        
        auth_data = response.json()
        token = auth_data.get("access_token")
        if not token:
            print("ERROR: No access token in response")
            raise ValueError("Authentication failed: No access token returned.")
        
        token_cache = token
        print("Successfully obtained new token")
        return token
    except Exception as e:
        print(f"Authentication failed: {str(e)}")
        traceback.print_exc()
        raise

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        # Handle root path
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'Proxy server is running. Use /proxy?url=<api-url> to make requests.')
            return
        
        # Handle proxy requests
        if self.path.startswith('/proxy'):
            # Extract the target URL from the query string
            query = self.path.split('?', 1)[1] if '?' in self.path else ''
            params = dict(param.split('=') for param in query.split('&') if '=' in param)
            
            if 'url' not in params:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Missing url parameter'}).encode('utf-8'))
                return
            
            # Decode the URL - this is crucial for handling encoded URLs
            encoded_url = params['url']
            print(f"Original encoded URL: {encoded_url}")
            
            target_url = urllib.parse.unquote(encoded_url)
            print(f"Decoded target URL: {target_url}")
            
            # Extract the issue_date for verification
            if 'issue_date=' in target_url:
                date_part = target_url.split('issue_date=')[1].split('&')[0] if '&' in target_url.split('issue_date=')[1] else target_url.split('issue_date=')[1]
                print(f"Extracted date from URL: {date_part}")
            else:
                print("No issue_date parameter found in URL")
            
            try:
                # Get authentication token
                token = get_auth_token()
                
                # Make request to the API
                response = requests.get(
                    target_url,
                    headers={
                        'Authorization': f'Bearer {token}',
                        'Content-Type': 'application/json'
                    }
                )
                response.raise_for_status()
                
                self.send_response(response.status_code)
                self.send_header('Content-type', response.headers.get('Content-Type', 'application/json'))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(response.content)
                
                print(f"--- NGI API Response for {target_url} ---")
                print(f"Status: {response.status_code}")
                # print(f"Headers: {response.headers}") # Optional, can be verbose
                try:
                    # Attempt to decode as UTF-8, log a snippet
                    response_content_snippet = response.content[:500].decode('utf-8', errors='ignore')
                    print(f"Data Snippet (first 500 chars decoded): {response_content_snippet}")

                    # Attempt to parse as JSON and log the 'meta' field if present
                    if response.headers.get('Content-Type') and 'application/json' in response.headers.get('Content-Type'):
                        json_data = response.json()
                        meta_info = json_data.get('meta')
                        print(f"Meta from JSON: {meta_info}")
                        # You could also log a few data points from json_data.get('data') if you want
                        # For example, if 'data' is a dictionary:
                        data_points = list(json_data.get('data', {}).keys())[:2] # Get first 2 data keys
                        print(f"Sample data keys: {data_points}")
                    else:
                        print("Response not JSON or Content-Type not set to application/json")

                except Exception as e:
                    print(f"Error processing/logging API response data: {e}")
                    print(f"Raw Data Snippet (first 500 bytes): {response.content[:500]}") # Log raw bytes if decoding/JSON parsing fails

                print(f"--------------------------------------")
                
            except requests.exceptions.RequestException as e:
                status_code = e.response.status_code if hasattr(e, 'response') and e.response is not None else 500
                self.send_error(status_code, str(e))
                print(f"Request error: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    print(f"Response: {e.response.text}")
            except Exception as e:
                self.send_error(500, f"Internal server error: {str(e)}")
                print(f"Error in do_GET: {e}")
                print(traceback.format_exc())
                
            return
        
        # Serve static files for all other paths
        try:
            file_path = os.path.join(os.getcwd(), self.path.lstrip('/'))
            with open(file_path, 'rb') as file:
                self.send_response(200)
                
                # Set content type based on file extension
                if file_path.endswith('.html'):
                    self.send_header('Content-type', 'text/html')
                elif file_path.endswith('.js'):
                    self.send_header('Content-type', 'application/javascript')
                elif file_path.endswith('.css'):
                    self.send_header('Content-type', 'text/css')
                else:
                    self.send_header('Content-type', 'application/octet-stream')
                    
                self.end_headers()
                self.wfile.write(file.read())
                
        except FileNotFoundError:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'File not found')

if __name__ == '__main__':
    PORT = 8081
    
    # Print important info at startup
    print("\n==== NGI API Proxy Server ====")
    print(f"Starting server on port {PORT}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Python version: {sys.version}")
    print("==============================\n")
    
    # Make sure we have credentials
    if not API_USERNAME or not API_PASSWORD:
        print("WARNING: Missing API credentials. Add NGI_API_USERNAME and NGI_API_PASSWORD to your .env file.")
        print("The .env file should be in this directory:", os.getcwd())
    else:
        print("API credentials found in .env file")
    
    try:
        with socketserver.TCPServer(("", PORT), ProxyHandler) as httpd:
            print(f"Proxy server running at http://localhost:{PORT}")
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("Stopping server...")
                httpd.shutdown()
    except Exception as e:
        print(f"Failed to start server: {str(e)}")
        traceback.print_exc()
