from flask import Flask, jsonify

app = Flask(__name__)

# In-memory data store for employees
employees = []

# ED-2: View Employee List
@app.route('/items', methods=['GET'])
def get_employees():
    return jsonify(employees), 200

# ED-4: Health Check
@app.route('/health', methods=['GET'])
def health_check():
    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)