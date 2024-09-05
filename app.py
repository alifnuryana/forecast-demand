from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
from prophet import Prophet
from datetime import datetime
import io
from flask_cors import CORS

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///transactions.db'
db = SQLAlchemy(app)

CORS(app)


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tanggal = db.Column(db.Date)
    nama_customer = db.Column(db.String(100))
    nama_barang = db.Column(db.String(100))
    jumlah_barang = db.Column(db.Integer)
    harga_satuan = db.Column(db.Float)
    total_pembayaran = db.Column(db.Float)
    size = db.Column(db.String(10))
    kategori = db.Column(db.String(50))


with app.app_context():
    db.create_all()


@app.route('/predict', methods=['POST'])
def predict():
    request_data = request.get_json()
    kategori = request_data['kategori']
    nama_barang = request_data['nama_barang']
    timeframe = request_data['timeframe']
    n_predictions = request_data['n_predictions']

    # Query the database for the relevant data
    filtered_data = Transaction.query.filter_by(kategori=kategori, nama_barang=nama_barang).all()

    # Convert to DataFrame
    data_dict = {
        'tanggal': [transaction.tanggal for transaction in filtered_data],
        'jumlah_barang': [transaction.jumlah_barang for transaction in filtered_data]
    }
    filtered_df = pd.DataFrame(data_dict)

    # Ensure date column is in the correct format
    filtered_df['tanggal'] = pd.to_datetime(filtered_df['tanggal'])
    filtered_df = filtered_df[['tanggal', 'jumlah_barang']].rename(columns={'tanggal': 'ds', 'jumlah_barang': 'y'})

    # Fit Prophet model and make predictions
    model = Prophet()
    model.fit(filtered_df)

    future = model.make_future_dataframe(periods=n_predictions, freq=timeframe)
    forecast = model.predict(future)

    # Extract forecast results including lower and upper bounds
    forecast_result = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(n_predictions)

    # Format date column to YYYY-MM-DD
    forecast_result['ds'] = forecast_result['ds'].dt.strftime('%Y-%m-%d')

    return jsonify(
        forecast_result.to_dict(orient='records')
    )


@app.route('/transaction', methods=['POST'])
def add_transaction():
    transaction_data = request.get_json()
    new_transaction = Transaction(
        tanggal=datetime.strptime(transaction_data['tanggal'], '%Y-%m-%d').date(),
        nama_customer=transaction_data['nama_customer'],
        nama_barang=transaction_data['nama_barang'],
        jumlah_barang=transaction_data['jumlah_barang'],
        harga_satuan=transaction_data['harga_satuan'],
        total_pembayaran=transaction_data['total_pembayaran'],
        size=transaction_data['size'],
        kategori=transaction_data['kategori']
    )

    with app.app_context():
        db.session.add(new_transaction)
        db.session.commit()

    return jsonify({'message': 'Transaction added successfully!'})


@app.route('/transaction/csv', methods=['POST'])
def add_transaction_csv():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and file.filename.endswith('.csv'):
        try:
            # Read the CSV file into a DataFrame
            file_content = file.read().decode('utf-8')
            data = pd.read_csv(io.StringIO(file_content))

            # Trim whitespace from all string columns in the DataFrame
            def trim_data(df):
                """Trim whitespace from all string columns in the DataFrame."""
                for col in df.select_dtypes(include=['object']).columns:
                    df[col] = df[col].str.strip()
                return df

            data = trim_data(data)

            # Process each row and add it to the database
            for _, row in data.iterrows():
                new_transaction = Transaction(
                    tanggal=datetime.strptime(row['tanggal'], '%Y-%m-%d').date(),
                    nama_customer=row['nama_customer'],
                    nama_barang=row['nama_barang'],
                    jumlah_barang=row['jumlah_barang'],
                    harga_satuan=row['harga_satuan'],
                    total_pembayaran=row['total_pembayaran'],
                    size=row['size'],
                    kategori=row['kategori']
                )
                db.session.add(new_transaction)
            db.session.commit()

            return jsonify({'message': 'Transactions added successfully!'})

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'Invalid file format'}), 400


@app.route('/categories', methods=['GET'])
def get_categories():
    categories = db.session.query(Transaction.kategori).distinct().all()
    categories_list = [category[0] for category in categories]
    return jsonify({'categories': categories_list})


@app.route('/items', methods=['GET'])
def get_items():
    category = request.args.get('category')
    if category:
        items = db.session.query(Transaction.nama_barang).filter_by(kategori=category).distinct().all()
    else:
        items = db.session.query(Transaction.nama_barang).distinct().all()

    items_list = [item[0] for item in items]
    return jsonify({'items': items_list})


if __name__ == '__main__':
    with app.app_context():
        app.run(debug=True, port=8000)
