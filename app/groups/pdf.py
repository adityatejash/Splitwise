import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

def generate_group_pdf(group, members, expenses, settlements, net_summary):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
    
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading3']
    normal_style = styles['Normal']
    
    elements = []
    
    # Title
    elements.append(Paragraph(f"Group Summary: {group.name}", title_style))
    if group.description:
        elements.append(Paragraph(group.description, normal_style))
    elements.append(Spacer(1, 20))
    
    # Members
    elements.append(Paragraph("Members", subtitle_style))
    member_data = [["Name", "Role", "Account Status"]]
    for m in members:
        member_data.append([
            m.name,
            m.role.capitalize(),
            "Registered" if m.is_registered else "No Account"
        ])
    t_members = Table(member_data, colWidths=[200, 100, 150])
    t_members.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E07A5F')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FAF7F2')),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(t_members)
    elements.append(Spacer(1, 20))
    
    # Expenses
    elements.append(Paragraph("Expenses", subtitle_style))
    if not expenses:
        elements.append(Paragraph("No expenses yet.", normal_style))
    else:
        totals_by_currency = {}
        exp_data = [["Date", "Description", "Paid By", "Amount"]]
        for e in expenses:
            c = e.currency
            amt = float(e.amount)
            totals_by_currency[c] = totals_by_currency.get(c, 0) + amt
            exp_data.append([
                e.expense_date.strftime("%d %b %Y"),
                e.description,
                e.payer.name,
                f"{c} {amt:.2f}"
            ])
            
        totals_str = " | ".join(f"{c} {amt:.2f}" for c, amt in totals_by_currency.items())
        elements.append(Paragraph(f"Total Group Spending: {totals_str}", normal_style))
        elements.append(Spacer(1, 10))
        
        t_exp = Table(exp_data, colWidths=[100, 200, 100, 100])
        t_exp.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3D405B')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(t_exp)
    
    elements.append(Spacer(1, 20))
    
    # Net Balances Summary
    elements.append(Paragraph("Net Balances", subtitle_style))
    net_data = [["Member", "Total Paid", "Total Owed", "Net Balance"]]
    for row in net_summary:
        net_data.append([
            row['name'],
            f"{row['total_paid']:.2f}",
            f"{row['total_owed']:.2f}",
            f"{row['net']:.2f}"
        ])
    t_net = Table(net_data, colWidths=[150, 100, 100, 100])
    t_net.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#81B29A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(t_net)
    elements.append(Spacer(1, 20))
    
    # Settlements
    elements.append(Paragraph("Suggested Settlements", subtitle_style))
    if not settlements:
        elements.append(Paragraph("All settled up! No one owes anything.", normal_style))
    else:
        settle_data = [["From", "To", "Amount"]]
        for s in settlements:
            settle_data.append([
                s['from_user'],
                s['to_user'],
                f"{s['currency']} {s['amount']:.2f}"
            ])
        t_settle = Table(settle_data, colWidths=[150, 150, 150])
        t_settle.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F2CC8F')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(t_settle)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer
