from flask import Flask, request, render_template_string, jsonify
import os
from cloudevents.http import from_http
import logging,json

logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')
port = int(os.environ.get("PORT", default=8080))
app = Flask(__name__)

# HTML template to display incoming requests
html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>HTTP POST Viewer</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 800px; margin: auto; }
        pre { background-color: #f4f4f4; padding: 10px; border: 1px solid #ddd; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Incoming HTTP POST Viewer</h1>
        <h2>Received Data:</h2>
        <pre>{{ event.data }}</pre>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def home():
    try:
        event = from_http(request.headers, request.get_data(),None)

        data = event.data
        # hack to handle non JSON payload, e.g. xml
        if not isinstance(data,dict):
            data = str(event.data)

        e = {
            "attributes": event._attributes,
            "data": data
        }
        app.logger.info(f'"***cloud event*** {json.dumps(e)}')
        return {}, 204
    except Exception as e:
        sc = 400
        msg = f'could not decode cloud event: {e}'
        app.logger.error(msg)
        message = {
            'status': sc,
            'error': msg,
        }
        resp = jsonify(message)
        resp.status_code = sc
        return resp
    return render_template_string(html_template, data=event.data)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Get port from environment variable or use default 5000
    app.run(debug=True, host='0.0.0.0', port=port)
