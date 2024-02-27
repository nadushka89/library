
from app import app

if __name__=='__main__':
    app.run(debug=True)

    # python -m flask db migrate
    # python -m flask db upgrade