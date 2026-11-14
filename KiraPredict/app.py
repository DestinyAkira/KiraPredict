import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-dev-key')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.get_json(silent=True) or {}
    try:
        base_rate = max(0.0, float(data.get('base_rate', 0)))
        reg_hours = max(0.0, float(data.get('regular_hours', 0)))
        ot_hours = max(0.0, float(data.get('ot_hours', 0)))
        double_hours = max(0.0, float(data.get('double_hours', 0)))
        triple_hours = max(0.0, float(data.get('triple_hours', 0)))
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid numeric input'}), 400

    regular_pay = base_rate * reg_hours
    ot_pay = (base_rate * 1.5) * ot_hours
    double_pay = (base_rate * 2.0) * double_hours
    triple_pay = (base_rate * 3.0) * triple_hours

    allowances_total = sum(
        max(0.0, float(item.get('rate', 0))) * max(0.0, float(item.get('qty', 0)))
        for item in data.get('allowances', [])
    )

    gross_pay = regular_pay + ot_pay + double_pay + triple_pay + allowances_total

    deductions_total = 0.0
    for item in data.get('deductions', []):
        val = max(0.0, float(item.get('rate', 0)))
        if item.get('type') == 'percent':
            deductions_total += gross_pay * (val / 100.0)
        else:
            deductions_total += val

    return jsonify({
        'gross_pay': round(gross_pay, 2),
        'net_pay': round(gross_pay - deductions_total, 2)
    })

if __name__ == '__main__':
    app.run(debug=False)