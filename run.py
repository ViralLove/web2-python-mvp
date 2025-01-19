from app import create_app
import requests
from flask import jsonify, request, Blueprint
print("Starting the application...")

test_bp = Blueprint('test', __name__)

# Create an instance of the application
app = create_app()

# make test API call "Hello World" via /hello
@test_bp.route('/hello', methods=['GET'])
def test_hello():
    data = request.get_json()
    message = data.get("message") if data else "Default Hello"
    return jsonify({"message": message})

# Entry point
if __name__ == '__main__':
    # Run the application with the specified host and port
    
    print("Starting the application...")
    app.run(host='0.0.0.0', port=5001, debug=True)

