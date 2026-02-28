import threading
from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
from flask_mail import Mail, Message
import database
import json
from datetime import date
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
import io

app = Flask(__name__)
app.secret_key = 'ayurvedic123'

# Email Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'ayurvedicdiet2026@gmail.com'
app.config['MAIL_PASSWORD'] = 'rxhd irek vfnk pkze'
app.config['MAIL_DEFAULT_SENDER'] = 'ayurvedicdiet2026@gmail.com'

mail = Mail(app)

food_nutrients = {
    'Rice':      {'unit': 'g',   'per': 100, 'calories': 130,  'protein': 2.7,  'carbs': 28,  'fats': 0.3,  'fiber': 0.4},
    'Roti':      {'unit': 'pcs', 'per': 1,   'calories': 80,   'protein': 2.5,  'carbs': 15,  'fats': 0.9,  'fiber': 0.7},
    'Dal':       {'unit': 'g',   'per': 100, 'calories': 116,  'protein': 9,    'carbs': 20,  'fats': 0.4,  'fiber': 8},
    'Moong Dal': {'unit': 'g',   'per': 100, 'calories': 347,  'protein': 24,   'carbs': 63,  'fats': 1.2,  'fiber': 16},
    'Paneer':    {'unit': 'g',   'per': 100, 'calories': 265,  'protein': 18,   'carbs': 1.2, 'fats': 20,   'fiber': 0},
    'Milk':      {'unit': 'ml',  'per': 100, 'calories': 61,   'protein': 3.2,  'carbs': 4.8, 'fats': 3.3,  'fiber': 0},
    'Curd':      {'unit': 'ml',  'per': 100, 'calories': 98,   'protein': 11,   'carbs': 3.4, 'fats': 4.3,  'fiber': 0},
    'Banana':    {'unit': 'pcs', 'per': 1,   'calories': 89,   'protein': 1.1,  'carbs': 23,  'fats': 0.3,  'fiber': 2.6},
    'Apple':     {'unit': 'pcs', 'per': 1,   'calories': 72,   'protein': 0.4,  'carbs': 19,  'fats': 0.2,  'fiber': 3.3},
    'Egg':       {'unit': 'pcs', 'per': 1,   'calories': 78,   'protein': 6,    'carbs': 0.6, 'fats': 5,    'fiber': 0},
    'Chicken':   {'unit': 'g',   'per': 100, 'calories': 165,  'protein': 31,   'carbs': 0,   'fats': 3.6,  'fiber': 0},
    'Ghee':      {'unit': 'tsp', 'per': 1,   'calories': 45,   'protein': 0,    'carbs': 0,   'fats': 5,    'fiber': 0},
    'Oats':      {'unit': 'g',   'per': 100, 'calories': 389,  'protein': 17,   'carbs': 66,  'fats': 7,    'fiber': 10},
    'Spinach':   {'unit': 'g',   'per': 100, 'calories': 23,   'protein': 2.9,  'carbs': 3.6, 'fats': 0.4,  'fiber': 2.2},
    'Potato':    {'unit': 'g',   'per': 100, 'calories': 77,   'protein': 2,    'carbs': 17,  'fats': 0.1,  'fiber': 2.2},
    'Cucumber':  {'unit': 'g',   'per': 100, 'calories': 16,   'protein': 0.7,  'carbs': 3.6, 'fats': 0.1,  'fiber': 0.5},
    'Tomato':    {'unit': 'pcs', 'per': 1,   'calories': 18,   'protein': 0.9,  'carbs': 3.9, 'fats': 0.2,  'fiber': 1.2},
    'Carrot':    {'unit': 'pcs', 'per': 1,   'calories': 25,   'protein': 0.6,  'carbs': 6,   'fats': 0.1,  'fiber': 1.7},
    'Idli':      {'unit': 'pcs', 'per': 1,   'calories': 39,   'protein': 2,    'carbs': 8,   'fats': 0.1,  'fiber': 0.5},
}

prakriti_foods = {
    'Vata': {
        'recommended': ['Warm milk', 'Ghee', 'Rice', 'Wheat', 'Sweet fruits', 'Root vegetables', 'Nuts', 'Sesame oil'],
        'avoid': ['Cold drinks', 'Raw vegetables', 'Dry fruits', 'Caffeine']
    },
    'Pitta': {
        'recommended': ['Coconut water', 'Cucumber', 'Sweet fruits', 'Leafy greens', 'Milk', 'Butter', 'Rice'],
        'avoid': ['Spicy food', 'Fried food', 'Alcohol', 'Red meat', 'Tomatoes']
    },
    'Kapha': {
        'recommended': ['Light grains', 'Honey', 'Ginger tea', 'Legumes', 'Spices', 'Bitter vegetables'],
        'avoid': ['Heavy food', 'Dairy', 'Sweets', 'Fried food', 'Cold food']
    }
}

weekly_plans = {
    'Vata': {
        'Monday':    {'breakfast': 'Warm oats (80g) + ghee (1tsp) + milk (250ml)', 'lunch': 'Rice (150g) + Dal (150g) + Spinach sabzi', 'snack': 'Banana (1) + warm milk (250ml)', 'dinner': 'Roti (2) + Moong Dal (150g) + Carrot sabzi'},
        'Tuesday':   {'breakfast': 'Idli (3) + sambhar + ghee (1tsp)', 'lunch': 'Roti (2) + Paneer (100g) + Dal (150g)', 'snack': 'Apple (1) + nuts', 'dinner': 'Rice (150g) + Dal (150g) + Potato sabzi'},
        'Wednesday': {'breakfast': 'Oats (80g) + banana (1) + milk (250ml)', 'lunch': 'Roti (2) + Chicken (150g) + salad', 'snack': 'Curd (200ml) + fruit', 'dinner': 'Roti (2) + Dal (150g) + Spinach sabzi'},
        'Thursday':  {'breakfast': 'Warm milk (250ml) + Roti (2) + ghee (1tsp)', 'lunch': 'Rice (150g) + Moong Dal (150g) + vegetables', 'snack': 'Banana (1) + warm tea', 'dinner': 'Roti (2) + Paneer (100g) + Dal (150g)'},
        'Friday':    {'breakfast': 'Idli (3) + coconut chutney + ghee (1tsp)', 'lunch': 'Roti (2) + Dal (150g) + Potato sabzi', 'snack': 'Apple (1) + milk (250ml)', 'dinner': 'Rice (150g) + Dal (150g) + Carrot sabzi'},
        'Saturday':  {'breakfast': 'Oats (80g) + milk (250ml) + ghee (1tsp)', 'lunch': 'Roti (2) + Egg (2) + salad', 'snack': 'Curd (200ml) + banana (1)', 'dinner': 'Roti (2) + Moong Dal (150g) + Spinach sabzi'},
        'Sunday':    {'breakfast': 'Warm milk (250ml) + Idli (3) + ghee (1tsp)', 'lunch': 'Rice (150g) + Chicken (150g) + Dal (150g)', 'snack': 'Banana (1) + nuts', 'dinner': 'Roti (2) + Paneer (100g) + vegetables'},
    },
    'Pitta': {
        'Monday':    {'breakfast': 'Oats (80g) + milk (250ml) + apple (1)', 'lunch': 'Rice (150g) + Moong Dal (150g) + Cucumber salad', 'snack': 'Coconut water + apple (1)', 'dinner': 'Roti (2) + Dal (150g) + Spinach sabzi'},
        'Tuesday':   {'breakfast': 'Idli (3) + coconut chutney', 'lunch': 'Roti (2) + Paneer (100g) + Cucumber salad', 'snack': 'Curd (200ml) + banana (1)', 'dinner': 'Rice (150g) + Moong Dal (150g) + Carrot sabzi'},
        'Wednesday': {'breakfast': 'Milk (250ml) + banana (1) + Roti (1)', 'lunch': 'Roti (2) + Dal (150g) + green salad', 'snack': 'Apple (1) + coconut water', 'dinner': 'Roti (2) + Paneer (100g) + Spinach sabzi'},
        'Thursday':  {'breakfast': 'Oats (80g) + milk (250ml)', 'lunch': 'Rice (150g) + Dal (150g) + Cucumber salad', 'snack': 'Curd (200ml) + apple (1)', 'dinner': 'Roti (2) + Moong Dal (150g) + vegetables'},
        'Friday':    {'breakfast': 'Idli (3) + mint chutney', 'lunch': 'Roti (2) + Dal (150g) + Spinach sabzi', 'snack': 'Banana (1) + milk (250ml)', 'dinner': 'Rice (150g) + Dal (150g) + Carrot sabzi'},
        'Saturday':  {'breakfast': 'Milk (250ml) + Roti (2)', 'lunch': 'Roti (2) + Paneer (100g) + salad', 'snack': 'Apple (1) + coconut water', 'dinner': 'Roti (2) + Dal (150g) + Spinach sabzi'},
        'Sunday':    {'breakfast': 'Oats (80g) + banana (1) + milk (250ml)', 'lunch': 'Rice (150g) + Dal (150g) + Cucumber salad', 'snack': 'Curd (200ml) + fruit', 'dinner': 'Roti (2) + Moong Dal (150g) + vegetables'},
    },
    'Kapha': {
        'Monday':    {'breakfast': 'Oats (80g) + ginger tea', 'lunch': 'Roti (1) + Moong Dal (150g) + Spinach sabzi', 'snack': 'Apple (1) + green tea', 'dinner': 'Roti (1) + Dal (150g) + Carrot sabzi'},
        'Tuesday':   {'breakfast': 'Idli (2) + sambhar (light)', 'lunch': 'Rice (100g) + Dal (150g) + vegetables', 'snack': 'Cucumber (100g) + lemon water', 'dinner': 'Roti (1) + Moong Dal (150g) + Spinach sabzi'},
        'Wednesday': {'breakfast': 'Oats (80g) + honey (1tsp) + ginger tea', 'lunch': 'Roti (1) + Chicken (150g) + salad', 'snack': 'Apple (1) + green tea', 'dinner': 'Roti (1) + Dal (150g) + vegetables'},
        'Thursday':  {'breakfast': 'Idli (2) + green chutney', 'lunch': 'Roti (1) + Dal (150g) + Spinach sabzi', 'snack': 'Carrot (1) + lemon water', 'dinner': 'Rice (100g) + Moong Dal (150g) + Carrot sabzi'},
        'Friday':    {'breakfast': 'Oats (80g) + ginger + honey (1tsp)', 'lunch': 'Roti (1) + Dal (150g) + vegetables', 'snack': 'Cucumber (100g) + green tea', 'dinner': 'Roti (1) + Dal (150g) + Spinach sabzi'},
        'Saturday':  {'breakfast': 'Idli (2) + sambhar (light)', 'lunch': 'Roti (1) + Chicken (150g) + salad', 'snack': 'Apple (1) + ginger tea', 'dinner': 'Roti (1) + Moong Dal (150g) + vegetables'},
        'Sunday':    {'breakfast': 'Oats (80g) + honey (1tsp) + milk (150ml)', 'lunch': 'Rice (100g) + Dal (150g) + Spinach sabzi', 'snack': 'Carrot (1) + lemon water', 'dinner': 'Roti (1) + Dal (150g) + Carrot sabzi'},
    }
}

def send_appointment_email(patient_email, patient_name, status, apt_date, apt_time, reason):
    def send_async():
        try:
            if status == 'Approved':
                subject = '✅ Appointment Approved - Ayurvedic Diet System'
                body = f'''
Dear {patient_name},

Your appointment has been APPROVED! 🎉

Appointment Details:
- Date: {apt_date}
- Time: {apt_time}
- Reason: {reason}

Please arrive 10 minutes early.

Thank you,
Ayurvedic Diet System Team
ayurvedicdiet2026@gmail.com
                '''
            else:
                subject = '❌ Appointment Rejected - Ayurvedic Diet System'
                body = f'''
Dear {patient_name},

We regret to inform you that your appointment has been REJECTED.

Appointment Details:
- Date: {apt_date}
- Time: {apt_time}
- Reason: {reason}

Please book a new appointment at a different time.

Thank you,
Ayurvedic Diet System Team
ayurvedicdiet2026@gmail.com
                '''
            with app.app_context():
                msg = Message(subject=subject, recipients=[patient_email], body=body)
                mail.send(msg)
        except Exception as e:
            print(f"Email error: {e}")

    thread = threading.Thread(target=send_async)
    thread.daemon = True
    thread.start()
    return True

def generate_appointment_pdf(report, appointment, doctor_note, diet_plan):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                            rightMargin=0.5*inch, leftMargin=0.5*inch,
                            topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    story = []

    header_style = ParagraphStyle('header', fontSize=20, textColor=colors.HexColor('#4a7c59'),
                                   spaceAfter=5, fontName='Helvetica-Bold', alignment=1)
    sub_style = ParagraphStyle('sub', fontSize=11, textColor=colors.grey,
                                spaceAfter=15, alignment=1)
    section_style = ParagraphStyle('section', fontSize=13, textColor=colors.HexColor('#4a7c59'),
                                    spaceAfter=8, fontName='Helvetica-Bold')

    story.append(Paragraph("Ayurvedic Diet System", header_style))
    story.append(Paragraph("Appointment Report", sub_style))
    story.append(Paragraph(f"Generated on: {date.today().strftime('%d %B %Y')}", sub_style))
    story.append(Spacer(1, 0.2*inch))

    # Patient Info
    story.append(Paragraph("Patient Information", section_style))
    patient_data = [
        ['Field', 'Details'],
        ['Patient ID', report[3] or 'N/A'],
        ['Full Name', report[0] or 'N/A'],
        ['Email', report[1] or 'N/A'],
        ['Phone', f"+91 {report[2]}" if report[2] else 'N/A'],
        ['Age', f"{report[4]} years" if report[4] else 'N/A'],
        ['Gender', report[5] or 'N/A'],
        ['BMI', f"{report[8]}" if report[8] else 'N/A'],
        ['Prakriti Type', report[9] or 'N/A'],
    ]
    table = Table(patient_data, colWidths=[2.5*inch, 4*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a7c59')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f0f7f0'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#4a7c59')),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.2*inch))

    # Appointment Details
    story.append(Paragraph("Appointment Details", section_style))
    apt_data = [
        ['Field', 'Details'],
        ['Date', appointment[5] or 'N/A'],
        ['Time', appointment[6] or 'N/A'],
        ['Reason', appointment[7] or 'N/A'],
        ['Status', appointment[8] or 'N/A'],
    ]
    apt_table = Table(apt_data, colWidths=[2.5*inch, 4*inch])
    apt_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a7c59')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f0f7f0'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#4a7c59')),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(apt_table)
    story.append(Spacer(1, 0.2*inch))

    # Doctor Note & Prescription
    if doctor_note:
        story.append(Paragraph("Doctor Notes & Prescription", section_style))
        notes_data = [
            ['Doctor Notes', 'Prescription'],
            [doctor_note[3] or 'N/A', doctor_note[4] or 'N/A']
        ]
        notes_table = Table(notes_data, colWidths=[4*inch, 4*inch])
        notes_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a7c59')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#f0f7f0')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#4a7c59')),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(notes_table)
        story.append(Spacer(1, 0.2*inch))
    else:
        story.append(Paragraph("Doctor Notes & Prescription", section_style))
        story.append(Paragraph("No doctor notes available for this appointment.", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))

    # Diet Plan
    if diet_plan and report[9]:
        story.append(Paragraph(f"Weekly Diet Plan ({report[9]} Prakriti)", section_style))
        plan_data = [['Day', 'Breakfast', 'Lunch', 'Snack', 'Dinner']]
        for day, meals in diet_plan.items():
            plan_data.append([
                day,
                meals.get('breakfast', ''),
                meals.get('lunch', ''),
                meals.get('snack', ''),
                meals.get('dinner', '')
            ])
        plan_table = Table(plan_data, colWidths=[0.8*inch, 2.2*inch, 2.2*inch, 1.8*inch, 2.2*inch])
        plan_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a7c59')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f0f7f0'), colors.white]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#4a7c59')),
            ('PADDING', (0, 0), (-1, -1), 4),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(plan_table)

    # Footer
    story.append(Spacer(1, 0.3*inch))
    footer_style = ParagraphStyle('footer', fontSize=9, textColor=colors.grey, alignment=1)
    story.append(Paragraph("Generated by Ayurvedic Diet System | ayurvedicdiet2026@gmail.com", footer_style))

    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_pdf_report(report, nutrient_log, diet_plan, doctor_notes):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                            rightMargin=0.5*inch, leftMargin=0.5*inch,
                            topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    story = []

    header_style = ParagraphStyle('header', fontSize=20, textColor=colors.HexColor('#4a7c59'),
                                   spaceAfter=5, fontName='Helvetica-Bold', alignment=1)
    sub_style = ParagraphStyle('sub', fontSize=11, textColor=colors.grey,
                                spaceAfter=15, alignment=1)
    section_style = ParagraphStyle('section', fontSize=13, textColor=colors.HexColor('#4a7c59'),
                                    spaceAfter=8, fontName='Helvetica-Bold')

    story.append(Paragraph("Ayurvedic Diet System", header_style))
    story.append(Paragraph("Patient Health Report", sub_style))
    story.append(Paragraph(f"Generated on: {date.today().strftime('%d %B %Y')}", sub_style))
    story.append(Spacer(1, 0.2*inch))

    # Patient Info
    story.append(Paragraph("Patient Information", section_style))
    patient_data = [
        ['Field', 'Details'],
        ['Patient ID', report[3] or 'N/A'],
        ['Full Name', report[0] or 'N/A'],
        ['Email', report[1] or 'N/A'],
        ['Phone', f"+91 {report[2]}" if report[2] else 'N/A'],
        ['Age', f"{report[4]} years" if report[4] else 'N/A'],
        ['Gender', report[5] or 'N/A'],
        ['Weight', f"{report[6]} kg" if report[6] else 'N/A'],
        ['Height', f"{report[7]} cm" if report[7] else 'N/A'],
        ['BMI', f"{report[8]}" if report[8] else 'N/A'],
        ['Prakriti Type', report[9] or 'N/A'],
    ]
    table = Table(patient_data, colWidths=[2.5*inch, 4*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a7c59')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f0f7f0'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#4a7c59')),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.2*inch))

    # Medical History
    if report[10] and report[10].strip().lower() not in ['na', 'n/a', 'none', '']:
        story.append(Paragraph("Medical History", section_style))
        story.append(Paragraph(report[10], styles['Normal']))
        story.append(Spacer(1, 0.2*inch))

    # Doctor Notes
    if doctor_notes:
        story.append(Paragraph("Doctor Notes & Prescription", section_style))
        notes_data = [['Date', 'Doctor Notes', 'Prescription']]
        for note in doctor_notes:
            notes_data.append([
                str(note[5])[:10],
                note[3] or 'N/A',
                note[4] or 'N/A'
            ])
        notes_table = Table(notes_data, colWidths=[1*inch, 3.5*inch, 3.5*inch])
        notes_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a7c59')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f0f7f0'), colors.white]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#4a7c59')),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(notes_table)
        story.append(Spacer(1, 0.2*inch))

    # Nutrient Log
    if nutrient_log:
        story.append(Paragraph("Latest Nutrient Analysis", section_style))
        nutrient_data = [
            ['Calories', 'Protein', 'Carbs', 'Fats', 'Fiber', 'Date'],
            [f"{nutrient_log[1]} kcal", f"{nutrient_log[2]}g",
             f"{nutrient_log[3]}g", f"{nutrient_log[4]}g",
             f"{nutrient_log[5]}g", str(nutrient_log[6])[:10]],
        ]
        n_table = Table(nutrient_data, colWidths=[1.3*inch]*6)
        n_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a7c59')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#f0f7f0')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#4a7c59')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(n_table)
        story.append(Spacer(1, 0.2*inch))

    # Diet Plan
    if diet_plan and report[9]:
        story.append(Paragraph(f"Weekly Diet Plan ({report[9]} Prakriti)", section_style))
        plan_data = [['Day', 'Breakfast', 'Lunch', 'Snack', 'Dinner']]
        for day, meals in diet_plan.items():
            plan_data.append([
                day,
                meals.get('breakfast', ''),
                meals.get('lunch', ''),
                meals.get('snack', ''),
                meals.get('dinner', '')
            ])
        plan_table = Table(plan_data, colWidths=[0.8*inch, 2.2*inch, 2.2*inch, 1.8*inch, 2.2*inch])
        plan_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a7c59')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f0f7f0'), colors.white]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#4a7c59')),
            ('PADDING', (0, 0), (-1, -1), 4),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(plan_table)

    # Footer
    story.append(Spacer(1, 0.3*inch))
    footer_style = ParagraphStyle('footer', fontSize=9, textColor=colors.grey, alignment=1)
    story.append(Paragraph("Generated by Ayurvedic Diet System | ayurvedicdiet2026@gmail.com", footer_style))

    doc.build(story)
    buffer.seek(0)
    return buffer

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        phone = request.form['phone']
        result, patient_id = database.register_user(name, email, password, role, phone)
        if result == "success":
            if patient_id:
                flash(f'Registration successful! Your Patient ID is {patient_id} — please save it!', 'success')
            else:
                flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Email already exists!', 'danger')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = database.login_user(email, password)
        if user:
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            session['user_role'] = user[4]
            session['patient_id'] = user[6] if len(user) > 6 else None
            flash(f'Welcome, {user[1]}!', 'success')
            if user[4] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user[4] == 'practitioner':
                return redirect(url_for('doctor_dashboard'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password!', 'danger')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    profile = database.get_patient_profile(session['user_id'])
    logs = database.get_nutrient_logs(session['user_id'])
    doctor_notes = database.get_doctor_notes(session['user_id'])
    return render_template('dashboard.html', name=session['user_name'],
                           profile=profile, patient_id=session.get('patient_id'),
                           logs=logs, doctor_notes=doctor_notes)

@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session['user_role'] != 'admin':
        return redirect(url_for('login'))
    users = database.get_all_users()
    all_appointments = database.get_all_appointments()
    stats = database.get_admin_stats()
    return render_template('admin_dashboard.html', name=session['user_name'],
                           users=users, all_appointments=all_appointments,
                           stats=stats)

@app.route('/admin/patient/<int:user_id>')
def admin_patient_details(user_id):
    if 'user_id' not in session or session['user_role'] != 'admin':
        return redirect(url_for('login'))
    details = database.get_patient_details(user_id)
    notes = database.get_all_doctor_notes_for_patient(user_id)
    return render_template('admin_patient_details.html', details=details, notes=notes)

@app.route('/admin/add_note/<int:user_id>', methods=['POST'])
def add_doctor_note(user_id):
    if 'user_id' not in session or session['user_role'] != 'admin':
        return redirect(url_for('login'))
    note = request.form['note']
    prescription = request.form['prescription']
    database.save_doctor_note(user_id, session['user_id'], note, prescription)
    flash('Doctor note added successfully!', 'success')
    return redirect(url_for('admin_patient_details', user_id=user_id))

@app.route('/admin/delete/<int:user_id>')
def admin_delete_user(user_id):
    if 'user_id' not in session or session['user_role'] != 'admin':
        return redirect(url_for('login'))
    database.delete_user(user_id)
    flash('User deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        age = request.form['age']
        gender = request.form['gender']
        weight = float(request.form['weight'])
        height = float(request.form['height'])
        medical_history = request.form['medical_history']
        prakriti = request.form['prakriti']
        bmi = database.save_patient_profile(
            session['user_id'], age, gender, weight, height, medical_history, prakriti
        )
        flash(f'Profile saved! Your BMI is {bmi}', 'success')
        return redirect(url_for('dashboard'))
    existing = database.get_patient_profile(session['user_id'])
    return render_template('profile.html', profile=existing)

@app.route('/nutrient', methods=['GET', 'POST'])
def nutrient():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    result = None
    if request.method == 'POST':
        selected_foods = request.form.getlist('foods')
        total = {'calories': 0, 'protein': 0, 'carbs': 0, 'fats': 0, 'fiber': 0}
        food_details = []
        for food in selected_foods:
            qty = float(request.form.get(f'qty_{food}', 1))
            if food in food_nutrients:
                n = food_nutrients[food]
                factor = qty / n['per']
                detail = {
                    'name': food,
                    'qty': qty,
                    'unit': n['unit'],
                    'calories': round(n['calories'] * factor, 1),
                    'protein': round(n['protein'] * factor, 1),
                    'carbs': round(n['carbs'] * factor, 1),
                    'fats': round(n['fats'] * factor, 1),
                    'fiber': round(n['fiber'] * factor, 1),
                }
                food_details.append(detail)
                total['calories'] += detail['calories']
                total['protein'] += detail['protein']
                total['carbs'] += detail['carbs']
                total['fats'] += detail['fats']
                total['fiber'] += detail['fiber']

        for key in total:
            total[key] = round(total[key], 1)

        food_items_str = ', '.join([f"{f['name']}({f['qty']}{f['unit']})" for f in food_details])
        database.save_nutrient_log(
            session['user_id'], food_items_str,
            total['calories'], total['protein'],
            total['carbs'], total['fats'], total['fiber']
        )
        result = {'foods': food_details, 'total': total}
        flash('Nutrient analysis saved successfully!', 'success')

    return render_template('nutrient.html',
                           food_list=[(k, v['unit']) for k, v in food_nutrients.items()],
                           result=result)

@app.route('/diet_plan')
def diet_plan():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    profile = database.get_patient_profile(session['user_id'])
    if not profile:
        flash('Please complete your profile first!', 'warning')
        return redirect(url_for('profile'))
    prakriti = profile[8]
    plan = weekly_plans.get(prakriti, {})
    database.save_diet_plan(session['user_id'], prakriti, json.dumps(plan))
    return render_template('diet_plan.html',
                           plan=plan,
                           prakriti=prakriti,
                           name=session['user_name'])

@app.route('/download_report')
def download_report():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    report = database.get_patient_full_report(session['user_id'])
    if not report:
        flash('Please complete your profile first!', 'warning')
        return redirect(url_for('profile'))
    nutrient_log = database.get_recent_nutrient_log(session['user_id'])
    doctor_notes = database.get_doctor_notes(session['user_id'])
    prakriti = report[9]
    diet_plan_data = weekly_plans.get(prakriti, {}) if prakriti else {}
    pdf_buffer = generate_pdf_report(report, nutrient_log, diet_plan_data, doctor_notes)
    response = make_response(pdf_buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=ayurvedic_report_{session.get("patient_id", "patient")}.pdf'
    return response

@app.route('/download_appointment_report/<int:appointment_id>')
def download_appointment_report(appointment_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    appointment = database.get_appointment_by_id_for_user(appointment_id, session['user_id'])
    if not appointment:
        flash('Appointment not found!', 'danger')
        return redirect(url_for('appointments'))
    report = database.get_patient_full_report(session['user_id'])
    if not report:
        flash('Please complete your profile first!', 'warning')
        return redirect(url_for('profile'))
    doctor_note = database.get_doctor_note_by_date(session['user_id'], appointment[5])
    prakriti = report[9]
    diet_plan_data = weekly_plans.get(prakriti, {}) if prakriti else {}
    pdf_buffer = generate_appointment_pdf(report, appointment, doctor_note, diet_plan_data)
    response = make_response(pdf_buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=appointment_report_{appointment_id}.pdf'
    return response

@app.route('/appointments', methods=['GET', 'POST'])
def appointments():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    today_date = date.today().strftime('%Y-%m-%d')
    doctors = database.get_doctors()

    time_slots = [
        '09:00-09:30', '09:30-10:00', '10:00-10:30', '10:30-11:00',
        '11:00-11:30', '11:30-12:00', '12:00-12:30', '12:30-01:00',
        '02:00-02:30', '02:30-03:00', '03:00-03:30', '03:30-04:00',
        '04:00-04:30', '04:30-05:00'
    ]

    if request.method == 'POST':
        patient_name = session['user_name']
        patient_id = session.get('patient_id', 'N/A')
        phone = request.form['phone']
        apt_date = request.form['date']
        apt_time = request.form['time']
        reason = request.form['reason']
        doctor_name = request.form['doctor_name']

        if not database.check_slot_available(doctor_name, apt_date, apt_time):
            flash(f'Sorry! {doctor_name}\'s {apt_time} slot on {apt_date} is already booked. Please select a different slot!', 'danger')
            return redirect(url_for('appointments'))

        database.book_appointment(
            session['user_id'], patient_name, patient_id, phone, apt_date, apt_time, reason, doctor_name
        )
        flash('Appointment booked successfully!', 'success')
        return redirect(url_for('appointments'))

    my_appointments = database.get_patient_appointments(session['user_id'])
    return render_template('appointments.html',
                           appointments=my_appointments,
                           is_admin=False,
                           today_date=today_date,
                           doctors=doctors,
                           time_slots=time_slots)

@app.route('/admin/appointments')
def admin_appointments():
    if 'user_id' not in session or session['user_role'] != 'admin':
        return redirect(url_for('login'))
    all_appointments = database.get_all_appointments()
    return render_template('appointments.html',
                           appointments=all_appointments,
                           is_admin=True,
                           today_date='')

@app.route('/admin/appointments/update/<int:appointment_id>/<status>')
def update_appointment(appointment_id, status):
    if 'user_id' not in session or session['user_role'] != 'admin':
        return redirect(url_for('login'))
    database.update_appointment_status(appointment_id, status)
    apt = database.get_appointment_by_id(appointment_id)
    if apt:
        patient_email = database.get_user_email(apt[1])
        if patient_email:
            sent = send_appointment_email(
                patient_email, apt[2], status, apt[5], apt[6], apt[7]
            )
            if sent:
                flash(f'Appointment {status}! Email sent to patient. 📧', 'success')
            else:
                flash(f'Appointment {status}! (Email could not be sent)', 'warning')
        else:
            flash(f'Appointment {status}!', 'success')
    return redirect(url_for('admin_appointments'))

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        if new_password != confirm_password:
            flash('New passwords do not match!', 'danger')
            return redirect(url_for('settings'))
        if len(new_password) < 6:
            flash('Password must be at least 6 characters!', 'danger')
            return redirect(url_for('settings'))
        result = database.change_password(session['user_id'], old_password, new_password)
        if result == "success":
            flash('Password changed successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Old password is incorrect!', 'danger')
    return render_template('settings.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        if new_password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('forgot_password'))
        if len(new_password) < 6:
            flash('Password must be at least 6 characters!', 'danger')
            return redirect(url_for('forgot_password'))
        result = database.reset_password_by_email(email, new_password)
        if result == "success":
            flash('Password reset successful! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Email not found!', 'danger')
    return render_template('forgot_password.html')

@app.route('/prakriti_result/<prakriti>')
def prakriti_result(prakriti):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    foods = prakriti_foods.get(prakriti, {})
    return render_template('prakriti_result.html', prakriti=prakriti, foods=foods)

@app.route('/doctor')
def doctor_dashboard():
    if 'user_id' not in session or session['user_role'] != 'practitioner':
        return redirect(url_for('login'))
    doctor_name = session['user_name']
    appointments = database.get_doctor_appointments(doctor_name)
    stats = database.get_doctor_stats(doctor_name)
    return render_template('doctor_dashboard.html',
                           name=session['user_name'],
                           appointments=appointments,
                           stats=stats)

@app.route('/doctor/appointments/update/<int:appointment_id>/<status>')
def doctor_update_appointment(appointment_id, status):
    if 'user_id' not in session or session['user_role'] != 'practitioner':
        return redirect(url_for('login'))
    database.update_appointment_status(appointment_id, status)
    apt = database.get_appointment_by_id(appointment_id)
    if apt:
        patient_email = database.get_user_email(apt[1])
        if patient_email:
            sent = send_appointment_email(
                patient_email, apt[2], status, apt[5], apt[6], apt[7]
            )
            if sent:
                flash(f'Appointment {status}! Email sent to patient. 📧', 'success')
            else:
                flash(f'Appointment {status}! (Email could not be sent)', 'warning')
    return redirect(url_for('doctor_dashboard'))

@app.route('/doctor/add_note/<int:user_id>', methods=['POST'])
def doctor_add_note(user_id):
    if 'user_id' not in session or session['user_role'] != 'practitioner':
        return redirect(url_for('login'))
    note = request.form['note']
    prescription = request.form['prescription']
    database.save_doctor_note(user_id, session['user_id'], note, prescription)
    flash('Note and prescription saved successfully!', 'success')
    return redirect(url_for('doctor_dashboard'))

@app.route('/doctor/patient/<int:user_id>')
def doctor_patient_details(user_id):
    if 'user_id' not in session or session['user_role'] != 'practitioner':
        return redirect(url_for('login'))
    details = database.get_patient_details(user_id)
    notes = database.get_all_doctor_notes_for_patient(user_id)
    return render_template('admin_patient_details.html',
                           details=details,
                           notes=notes,
                           is_doctor=True)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

import os

with app.app_context():
    database.init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
Save karo. Git Bash mein: