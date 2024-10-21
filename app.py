from flask import Flask
from models import db
from routes import api_blueprint

app = Flask(__name__)


app.config.from_object('config.Config')

# Add a simple secret key for testing
app.config['SECRET_KEY'] = 'test_secret_key'

# Initialize the databasey
db.init_app(app)

# Register the routes
app.register_blueprint(api_blueprint)

# Create the database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run()
