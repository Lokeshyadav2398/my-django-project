# Social Networking API

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository_url>
   cd <repository_name>

python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

pip install -r requirements.txt

python manage.py migrate

python manage.py runserver

docker-compose up --build