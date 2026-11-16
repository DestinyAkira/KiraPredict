from datetime import datetime
import io
from flask import Flask, jsonify, render_template, request, send_file
from flask_sqlalchemy import SQLAlchemy
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

app = Flask(__name__)

# Configure SQLite Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kirazpredict.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class ShiftRecord(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  day_id = db.Column(db.String(10), nullable=False)
  day_name = db.Column(db.String(20), nullable=False)
  shift_date = db.Column(db.String(20), default='')
  start_time = db.Column(db.String(10), default='08:00')
  finish_time = db.Column(db.String(10), default='17:00')
  holiday_tier = db.Column(db.Float, default=1.0)
  status_type = db.Column(db.String(20), default='normal')
  ramp_allowance = db.Column(db.Boolean, default=False)
  is_worked = db.Column(db.Boolean, default=True)
  created_at = db.Column(db.DateTime, default=datetime.utcnow)

  def to_dict(self):
    return {
        'id': self.id,
        'day_id': self.day_id,
        'day_name': self.day_name,
        'shift_date': self.shift_date,
        'start_time': self.start_time,
        'finish_time': self.finish_time,
        'holiday_tier': self.holiday_tier,
        'status_type': self.status_type,
        'ramp_allowance': self.ramp_allowance,
        'is_worked': self.is_worked,
    }


with app.app_context():
  db.create_all()


@app.route('/')
def index():
  return render_template('index.html')


@app.route('/api/shifts', methods=['GET'])
def get_shifts():
  shifts = ShiftRecord.query.all()
  return jsonify([s.to_dict() for s in shifts])


@app.route('/api/shifts', methods=['POST'])
def save_shifts():
  data = request.get_json()
  ShiftRecord.query.delete()

  for item in data.get('shifts', []):
    new_shift = ShiftRecord(
        day_id=item.get('day_id'),
        day_name=item.get('day_name'),
        shift_date=item.get('shift_date', ''),
        start_time=item.get('start_time'),
        finish_time=item.get('finish_time'),
        holiday_tier=float(item.get('holiday_tier', 1.0)),
        status_type=item.get('status_type', 'normal'),
        ramp_allowance=bool(item.get('ramp_allowance', False)),
        is_worked=bool(item.get('is_worked', True)),
    )
    db.session.add(new_shift)

  db.session.commit()
  return jsonify({'status': 'success', 'message': 'Shifts saved successfully!'})


@app.route('/api/download-payslip', methods=['POST'])
def download_payslip():
  data = request.get_json() or {}

  week_start = data.get('week_start', 'N/A')
  net_total = data.get('net_total', '$0.00')

  reg_text = data.get('reg_text', '0 hrs @ $0.00')
  reg_amt = data.get('reg_amt', '$0.00')

  ot_text = data.get('ot_text', '0 hrs @ $0.00')
  ot_amt = data.get('ot_amt', '$0.00')

  dt_text = data.get('dt_text', '0 hrs @ $0.00')
  dt_amt = data.get('dt_amt', '$0.00')

  tt_text = data.get('tt_text', '0 hrs @ $0.00')
  tt_amt = data.get('tt_amt', '$0.00')

  early_text = data.get('early_text', '0 @ $15.00')
  early_amt = data.get('early_amt', '$0.00')

  meal_text = data.get('meal_text', '0 @ $20.00')
  meal_amt = data.get('meal_amt', '$0.00')

  ramp_text = data.get('ramp_text', '0 @ $16.00')
  ramp_amt = data.get('ramp_amt', '$0.00')

  nis_amt = data.get('nis_amt', '$0.00')

  buffer = io.BytesIO()
  doc = SimpleDocTemplate(
      buffer,
      pagesize=letter,
      rightMargin=36,
      leftMargin=36,
      topMargin=36,
      bottomMargin=36,
  )
  styles = getSampleStyleSheet()
  story = []

  title_style = ParagraphStyle(
      'TitleStyle',
      parent=styles['Heading1'],
      fontSize=18,
      textColor=colors.HexColor('#059669'),
      spaceAfter=4,
  )
  story.append(Paragraph('KiraZPredict &bull; Barbadian Wage Statement', title_style))
  story.append(
      Paragraph(
          f'<b>Week Starting (Sunday):</b> {week_start}', styles['Normal']
      )
  )
  story.append(Spacer(1, 15))

  table_data = [
      ['Category / Item', 'Calculation Detail', 'Amount (BBD)'],
      ['Regular Pay', reg_text, reg_amt],
      ['Overtime Pay', ot_text, ot_amt],
      ['Double Pay', dt_text, dt_amt],
      ['Triple Pay', tt_text, tt_amt],
      ['Allowance: Early', early_text, early_amt],
      ['Allowance: Meal', meal_text, meal_amt],
      ['Allowance: Ramp', ramp_text, ramp_amt],
      ['NIS Deduction (11.1%)', '11.1% of Gross', f'-{nis_amt}'],
      ['Estimated Net Payout', '', net_total],
  ]

  t = Table(table_data, colWidths=[140, 240, 120])
  t.setStyle(
      TableStyle([
          ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
          ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
          ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
          ('FONTSIZE', (0, 0), (-1, 0), 9),
          ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
          ('TOPPADDING', (0, 0), (-1, 0), 6),
          ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ecfdf5')),
          ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
          ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#065f46')),
          ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
          ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
          ('FONTSIZE', (0, 1), (-1, -1), 8.5),
      ])
  )

  story.append(t)
  story.append(Spacer(1, 20))
  story.append(
      Paragraph(
          '<font size=8 color="#64748b">Generated automatically by KiraZPredict'
          ' &bull; Compliant with Barbadian Wage & NIS Guidelines</font>',
          styles['Normal'],
      )
  )

  doc.build(story)
  buffer.seek(0)
  return send_file(
      buffer,
      as_attachment=True,
      download_name='KiraZPredict_Payslip.pdf',
      mimetype='application/pdf',
  )


if __name__ == '__main__':
  app.run(debug=True)