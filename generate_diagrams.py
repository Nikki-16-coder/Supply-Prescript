import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

os.makedirs('scratch_report_assets', exist_ok=True)

def generate_flowchart():
    fig, ax = plt.subplots(figsize=(8, 10), dpi=200)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 14)
    ax.axis('off')
    
    # Title
    ax.text(5, 13.5, "SupplyPrescript Operational Flowchart", ha='center', va='center', fontsize=14, fontweight='bold', fontfamily='serif')
    
    # Node boxes: (text, x, y, width, height, shape_type, color)
    nodes = [
        ("Start: Ingest Shipment & Fab Telemetry", 5, 12.5, 5.0, 0.7, 'oval', '#E1F5FE', '#0288D1'),
        ("Feature Engineering & Preprocessing\n(Origin, SKU, Lead Time, Carrier Reliability)", 5, 11.2, 5.4, 0.9, 'box', '#E8F5E9', '#388E3C'),
        ("XGBoost Pre-Transit Inference Engine\nCompute Delay Probability P(Delay)", 5, 9.8, 5.2, 0.9, 'box', '#E8F5E9', '#388E3C'),
        ("Is Delay Probability\nP(Delay) >= 0.50?", 5, 8.2, 4.2, 1.2, 'diamond', '#FFF9C4', '#FBC02D'),
        ("Standard Ground/Ocean Logistics Pipeline\n(Regular In-Transit Tracking)", 1.8, 6.6, 3.2, 1.0, 'box', '#F3E5F5', '#7B1FA2'),
        ("Formulate Prescriptive MILP Model\n(Cost Ceiling, SLAs, Buffer Stock, Air Freight)", 6.8, 6.6, 4.4, 1.0, 'box', '#E3F2FD', '#1976D2'),
        ("Execute PuLP Solver (CBC Engine)\nMinimize Disruption Recovery Cost", 6.8, 5.0, 4.4, 0.9, 'box', '#E3F2FD', '#1976D2'),
        ("Generate Optimal Decision Action Plan\n(Air Expedite / Split Route / Buffer Draw)", 6.8, 3.6, 4.4, 0.9, 'box', '#EDE7F6', '#512DA8'),
        ("Manager Review & Automated Audit Log\nRecord Decision in Database", 5, 2.2, 5.2, 0.9, 'box', '#FFF3E0', '#F57C00'),
        ("Closed-Loop Feedback: Record Actual Arrival\n& Update Optimization Telemetry", 5, 0.9, 5.2, 0.8, 'oval', '#ECEFF1', '#455A64')
    ]
    
    for text, cx, cy, w, h, stype, bg, border in nodes:
        if stype == 'oval':
            patch = patches.FancyBboxPatch((cx - w/2, cy - h/2), w, h, boxstyle="round,pad=0.2", fc=bg, ec=border, lw=2)
            ax.add_patch(patch)
        elif stype == 'box':
            patch = patches.FancyBboxPatch((cx - w/2, cy - h/2), w, h, boxstyle="square,pad=0.1", fc=bg, ec=border, lw=1.8)
            ax.add_patch(patch)
        elif stype == 'diamond':
            poly = patches.Polygon([[cx, cy + h/2], [cx + w/2, cy], [cx, cy - h/2], [cx - w/2, cy]], closed=True, fc=bg, ec=border, lw=2)
            ax.add_patch(poly)
        ax.text(cx, cy, text, ha='center', va='center', fontsize=9, fontfamily='serif', fontweight='bold', color='#1A237E' if border!='#388E3C' else '#1B5E20')

    # Arrows
    def arrow(x1, y1, x2, y2, label=""):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", color="#37474F", lw=1.5))
        if label:
            mx, my = (x1 + x2)/2, (y1 + y2)/2
            ax.text(mx + 0.15, my, label, fontsize=8.5, fontweight='bold', color='#B71C1C', fontfamily='serif')

    arrow(5, 12.15, 5, 11.65)
    arrow(5, 10.75, 5, 10.25)
    arrow(5, 9.35, 5, 8.8)
    
    # Diamond branches
    # No -> left
    ax.plot([2.9, 1.8], [8.2, 8.2], color="#37474F", lw=1.5)
    arrow(1.8, 8.2, 1.8, 7.1, "No")
    
    # Yes -> right
    ax.plot([7.1, 6.8], [8.2, 8.2], color="#37474F", lw=1.5)
    arrow(6.8, 8.2, 6.8, 7.1, "Yes")
    
    arrow(6.8, 6.1, 6.8, 5.45)
    arrow(6.8, 4.55, 6.8, 4.05)
    
    # Join into manager review
    ax.plot([1.8, 1.8, 4.0], [6.1, 2.2, 2.2], color="#37474F", lw=1.5)
    arrow(4.0, 2.2, 5.0 - 2.6, 2.2)
    
    ax.plot([6.8, 6.8, 6.0], [3.15, 2.2, 2.2], color="#37474F", lw=1.5)
    arrow(6.0, 2.2, 5.0 + 2.6, 2.2)
    
    arrow(5, 1.75, 5, 1.3)
    
    plt.tight_layout()
    plt.savefig('scratch_report_assets/flowchart.png', dpi=200, bbox_inches='tight')
    plt.close()
    print("Generated flowchart.png")

def generate_dfd():
    fig, ax = plt.subplots(figsize=(9, 6.5), dpi=200)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.axis('off')
    
    ax.text(6, 7.6, "Level 0 Context Data Flow Diagram (DFD)", ha='center', va='center', fontsize=13, fontweight='bold', fontfamily='serif')
    
    # Central Process
    circ = patches.Circle((6, 4), 1.5, fc='#E1F5FE', ec='#0288D1', lw=2.5)
    ax.add_patch(circ)
    ax.text(6, 4.3, "0.0", ha='center', va='center', fontsize=12, fontweight='bold', fontfamily='serif')
    ax.text(6, 3.8, "SupplyPrescript\nSystem", ha='center', va='center', fontsize=11, fontweight='bold', fontfamily='serif')
    
    # External Entities
    entities = [
        ("Fab / Carrier\nEDI Feed", 1.5, 6, 2.2, 1.2),
        ("Logistics\nAnalyst", 1.5, 2, 2.2, 1.2),
        ("Supply Chain\nManager", 10.5, 6, 2.2, 1.2),
        ("Enterprise\nERP / TMS", 10.5, 2, 2.2, 1.2)
    ]
    
    for name, x, y, w, h in entities:
        rect = patches.Rectangle((x - w/2, y - h/2), w, h, fc='#FFF3E0', ec='#E65100', lw=2)
        ax.add_patch(rect)
        ax.text(x, y, name, ha='center', va='center', fontsize=9.5, fontweight='bold', fontfamily='serif')
        
    # Data flows
    # Carrier -> Process
    ax.annotate('', xy=(4.6, 4.8), xytext=(2.6, 5.8), arrowprops=dict(arrowstyle="->", color="#37474F", lw=1.5))
    ax.text(3.3, 5.5, "Shipment Telemetry", fontsize=8, fontweight='bold', fontfamily='serif')
    
    # Analyst -> Process
    ax.annotate('', xy=(4.6, 3.4), xytext=(2.6, 2.4), arrowprops=dict(arrowstyle="->", color="#37474F", lw=1.5))
    ax.text(3.1, 2.7, "Manual Override / Queries", fontsize=8, fontweight='bold', fontfamily='serif')
    
    # Process -> Analyst
    ax.annotate('', xy=(2.6, 1.8), xytext=(4.6, 3.0), arrowprops=dict(arrowstyle="->", color="#1565C0", lw=1.5, linestyle="--"))
    ax.text(3.0, 2.1, "Risk Alerts & Status", fontsize=8, color="#1565C0", fontweight='bold', fontfamily='serif')
    
    # Process -> Manager
    ax.annotate('', xy=(9.4, 5.8), xytext=(7.4, 4.8), arrowprops=dict(arrowstyle="->", color="#37474F", lw=1.5))
    ax.text(7.7, 5.5, "Prescriptive Plans & KPIs", fontsize=8, fontweight='bold', fontfamily='serif')
    
    # Manager -> Process
    ax.annotate('', xy=(7.3, 4.4), xytext=(9.4, 5.3), arrowprops=dict(arrowstyle="->", color="#D84315", lw=1.5, linestyle="--"))
    ax.text(7.6, 4.7, "Approval & Cost Ceilings", fontsize=8, color="#D84315", fontweight='bold', fontfamily='serif')
    
    # Process -> ERP
    ax.annotate('', xy=(9.4, 2.3), xytext=(7.4, 3.4), arrowprops=dict(arrowstyle="->", color="#2E7D32", lw=1.5))
    ax.text(7.7, 3.1, "Updated Routing & PO Orders", fontsize=8, color="#2E7D32", fontweight='bold', fontfamily='serif')
    
    plt.tight_layout()
    plt.savefig('scratch_report_assets/dfd_context.png', dpi=200, bbox_inches='tight')
    plt.close()
    print("Generated dfd_context.png")

def generate_er():
    fig, ax = plt.subplots(figsize=(9, 6.5), dpi=200)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.axis('off')
    
    ax.text(6, 7.6, "Entity-Relationship (ER) Diagram", ha='center', va='center', fontsize=13, fontweight='bold', fontfamily='serif')
    
    # Entities (rectangles)
    ents = [
        ("USERS\n[user_id, email,\nrole, hashed_pw]", 2.0, 5.5, 2.6, 1.4),
        ("SHIPMENTS\n[shipment_id, sku,\norigin, dest, lead_time]", 6.0, 5.5, 2.8, 1.4),
        ("PREDICTIONS\n[prediction_id, delay_prob,\nrisk_level, model_ver]", 10.0, 5.5, 2.8, 1.4),
        ("OPTIMIZATION_DECISIONS\n[decision_id, action_type,\nair_expedite, cost_est]", 6.0, 1.8, 3.2, 1.4),
        ("OUTCOMES\n[outcome_id, actual_delay,\nactual_cost, variance]", 10.0, 1.8, 2.8, 1.4)
    ]
    
    for text, x, y, w, h in ents:
        rect = patches.Rectangle((x - w/2, y - h/2), w, h, fc='#E8EAF6', ec='#283593', lw=2)
        ax.add_patch(rect)
        ax.text(x, y, text, ha='center', va='center', fontsize=8.5, fontweight='bold', fontfamily='serif')
        
    # Relationship Diamonds
    rels = [
        ("Monitors", 4.0, 5.5, 1.2, 0.8),
        ("Assesses", 8.0, 5.5, 1.2, 0.8),
        ("Prescribes", 6.0, 3.6, 1.2, 0.8),
        ("Evaluates", 10.0, 3.6, 1.2, 0.8)
    ]
    
    for text, x, y, w, h in rels:
        diamond = patches.Polygon([[x, y+h/2], [x+w/2, y], [x, y-h/2], [x-w/2, y]], closed=True, fc='#FFF9C4', ec='#F57F17', lw=1.5)
        ax.add_patch(diamond)
        ax.text(x, y, text, ha='center', va='center', fontsize=7.5, fontweight='bold', fontfamily='serif')
        
    # Lines
    ax.plot([3.3, 4.0-0.6], [5.5, 5.5], color='#37474F', lw=1.5)
    ax.plot([4.0+0.6, 6.0-1.4], [5.5, 5.5], color='#37474F', lw=1.5)
    ax.text(3.5, 5.7, "1", fontsize=9, fontweight='bold')
    ax.text(4.4, 5.7, "M", fontsize=9, fontweight='bold')
    
    ax.plot([6.0+1.4, 8.0-0.6], [5.5, 5.5], color='#37474F', lw=1.5)
    ax.plot([8.0+0.6, 10.0-1.4], [5.5, 5.5], color='#37474F', lw=1.5)
    ax.text(7.5, 5.7, "1", fontsize=9, fontweight='bold')
    ax.text(8.4, 5.7, "1", fontsize=9, fontweight='bold')
    
    ax.plot([6.0, 6.0], [5.5-0.7, 3.6+0.4], color='#37474F', lw=1.5)
    ax.plot([6.0, 6.0], [3.6-0.4, 1.8+0.7], color='#37474F', lw=1.5)
    ax.text(6.15, 4.4, "1", fontsize=9, fontweight='bold')
    ax.text(6.15, 2.8, "1", fontsize=9, fontweight='bold')
    
    ax.plot([10.0, 10.0], [5.5-0.7, 3.6+0.4], color='#37474F', lw=1.5)
    ax.plot([10.0, 10.0], [3.6-0.4, 1.8+0.7], color='#37474F', lw=1.5)
    ax.text(10.15, 4.4, "1", fontsize=9, fontweight='bold')
    ax.text(10.15, 2.8, "1", fontsize=9, fontweight='bold')

    plt.tight_layout()
    plt.savefig('scratch_report_assets/er_diagram.png', dpi=200, bbox_inches='tight')
    plt.close()
    print("Generated er_diagram.png")

def generate_screenshots():
    # 1. Login screenshot
    fig, ax = plt.subplots(figsize=(10, 6), dpi=200)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')
    
    # Outer frame
    frame = patches.Rectangle((0.2, 0.2), 9.6, 5.6, fc='#0F172A', ec='#334155', lw=2)
    ax.add_patch(frame)
    # Left Hero Panel
    hero = patches.Rectangle((0.2, 0.2), 4.8, 5.6, fc='#1E293B', ec='#334155', lw=1.5)
    ax.add_patch(hero)
    ax.text(0.6, 4.8, "SupplyPrescript", fontsize=18, fontweight='bold', color='#38BDF8', fontfamily='sans-serif')
    ax.text(0.6, 4.2, "Enterprise Disruption Intelligence", fontsize=11, color='#94A3B8', fontfamily='sans-serif')
    ax.text(0.6, 3.2, "Predict Disruption.\nPrescribe Recovery.", fontsize=15, fontweight='bold', color='#F8FAFC', fontfamily='sans-serif')
    ax.text(0.6, 2.2, "Next-generation prescriptive engine\nfor semiconductor supply chain resilience.\nCombines XGBoost pre-transit ML\nwith Mixed-Integer Linear Programming.", fontsize=9, color='#CBD5E1', fontfamily='sans-serif')
    
    # Right Form Panel
    ax.text(5.4, 4.8, "Sign In to Your Workspace", fontsize=14, fontweight='bold', color='#F8FAFC', fontfamily='sans-serif')
    ax.text(5.4, 4.4, "Select your preferred authentication method", fontsize=9, color='#94A3B8', fontfamily='sans-serif')
    
    # Google Button
    g_btn = patches.FancyBboxPatch((5.4, 3.5), 4.0, 0.6, boxstyle="round,pad=0.08", fc='#1E293B', ec='#475569', lw=1.5)
    ax.add_patch(g_btn)
    ax.text(7.4, 3.8, "[G]  Sign in with Google", ha='center', va='center', fontsize=9.5, fontweight='bold', color='#F8FAFC', fontfamily='sans-serif')
    
    # Facebook Button
    fb_btn = patches.FancyBboxPatch((5.4, 2.7), 4.0, 0.6, boxstyle="round,pad=0.08", fc='#1E293B', ec='#475569', lw=1.5)
    ax.add_patch(fb_btn)
    ax.text(7.4, 3.0, "[f]  Sign in with Facebook", ha='center', va='center', fontsize=9.5, fontweight='bold', color='#38BDF8', fontfamily='sans-serif')
    
    # Divider
    ax.plot([5.4, 9.4], [2.3, 2.3], color='#334155', lw=1)
    ax.text(7.4, 2.3, "  or sign in with email  ", ha='center', va='center', fontsize=8, color='#64748B', backgroundcolor='#0F172A', fontfamily='sans-serif')
    
    # Email input
    e_box = patches.Rectangle((5.4, 1.5), 4.0, 0.5, fc='#1E293B', ec='#475569', lw=1)
    ax.add_patch(e_box)
    ax.text(5.6, 1.75, "analyst@enterprise.com", va='center', fontsize=8.5, color='#94A3B8', fontfamily='sans-serif')
    
    # Sign In Button
    s_btn = patches.FancyBboxPatch((5.4, 0.7), 4.0, 0.55, boxstyle="round,pad=0.06", fc='#0284C7', ec='#0284C7', lw=1)
    ax.add_patch(s_btn)
    ax.text(7.4, 0.97, "Sign In with Password", ha='center', va='center', fontsize=9.5, fontweight='bold', color='#FFFFFF', fontfamily='sans-serif')
    
    plt.tight_layout()
    plt.savefig('scratch_report_assets/screenshot_login.png', dpi=200, bbox_inches='tight')
    plt.close()
    
    # 2. Dashboard screenshot
    fig, ax = plt.subplots(figsize=(10, 6), dpi=200)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')
    
    bg = patches.Rectangle((0, 0), 10, 6, fc='#0F172A', ec='#334155', lw=2)
    ax.add_patch(bg)
    
    # Navbar
    nav = patches.Rectangle((0, 5.3), 10, 0.7, fc='#1E293B', ec='#334155', lw=1)
    ax.add_patch(nav)
    ax.text(0.5, 5.65, "SupplyPrescript  |  Operations Command Center", fontsize=12, fontweight='bold', color='#38BDF8', va='center', fontfamily='sans-serif')
    ax.text(9.2, 5.65, "Role: Manager", fontsize=9, color='#94A3B8', ha='right', va='center', fontfamily='sans-serif')
    
    # Metric cards
    cards = [
        ("Active Shipments", "1,428", "#38BDF8", 0.5, 4.0, 2.0, 1.0),
        ("High Delay Risk", "47", "#EF4444", 2.8, 4.0, 2.0, 1.0),
        ("Prescriptions Pending", "12", "#F59E0B", 5.1, 4.0, 2.0, 1.0),
        ("Disruption Cost Saved", "$142,500", "#10B981", 7.4, 4.0, 2.1, 1.0)
    ]
    for title, val, color, x, y, w, h in cards:
        c_box = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08", fc='#1E293B', ec='#334155', lw=1.5)
        ax.add_patch(c_box)
        ax.text(x + w/2, y + 0.7, title, fontsize=8, color='#94A3B8', ha='center', fontfamily='sans-serif')
        ax.text(x + w/2, y + 0.3, val, fontsize=14, fontweight='bold', color=color, ha='center', fontfamily='sans-serif')
        
    # Table panel
    tbl = patches.Rectangle((0.5, 0.5), 9.0, 3.2, fc='#1E293B', ec='#334155', lw=1.5)
    ax.add_patch(tbl)
    ax.text(0.8, 3.4, "Real-Time Pre-Transit Disruption Ingestion Queue", fontsize=10, fontweight='bold', color='#F8FAFC', fontfamily='sans-serif')
    
    headers = ["Shipment ID", "SKU Category", "Origin Fab", "Dest Hub", "Delay Prob", "Risk Level", "Status"]
    xs = [0.8, 2.0, 3.5, 5.0, 6.3, 7.5, 8.7]
    for h_txt, hx in zip(headers, xs):
        ax.text(hx, 3.0, h_txt, fontsize=8, fontweight='bold', color='#94A3B8', fontfamily='sans-serif')
    ax.plot([0.7, 9.3], [2.85, 2.85], color='#475569', lw=1)
    
    rows = [
        ("SHP-88219", "Automotive MCU", "Taiwan Fab 1", "Detroit Hub", "84.2%", "CRITICAL", "Prescribing..."),
        ("SHP-88220", "Power PMIC 7nm", "Hsinchu Park", "Munich Hub", "76.5%", "HIGH", "Review Plan"),
        ("SHP-88221", "RF Transceiver", "Dresden Fab", "Austin Hub", "21.0%", "LOW", "Standard Route"),
        ("SHP-88222", "High-Bandwidth RAM", "Suwon Plant", "Penang Hub", "12.4%", "LOW", "Standard Route"),
        ("SHP-88223", "SoC Sensor ASIC", "Grenoble Hub", "Shenzhen Hub", "68.9%", "HIGH", "Review Plan")
    ]
    for idx, r_data in enumerate(rows):
        ry = 2.5 - idx * 0.4
        c_risk = '#EF4444' if 'CRITICAL' in r_data[5] else ('#F59E0B' if 'HIGH' in r_data[5] else '#10B981')
        for val, vx in zip(r_data, xs):
            col = c_risk if val in ['CRITICAL', 'HIGH', 'LOW'] else '#E2E8F0'
            ax.text(vx, ry, val, fontsize=8, color=col, fontfamily='sans-serif')
            
    plt.tight_layout()
    plt.savefig('scratch_report_assets/screenshot_dashboard.png', dpi=200, bbox_inches='tight')
    plt.close()
    
    # 3. Optimization screenshot
    fig, ax = plt.subplots(figsize=(10, 6), dpi=200)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')
    
    bg = patches.Rectangle((0, 0), 10, 6, fc='#0F172A', ec='#334155', lw=2)
    ax.add_patch(bg)
    
    # Header
    ax.text(0.5, 5.5, "PuLP Mixed-Integer Linear Programming Prescriptive Decision Matrix", fontsize=12, fontweight='bold', color='#38BDF8', fontfamily='sans-serif')
    ax.text(0.5, 5.15, "Target Disruption: SHP-88219 (Automotive MCU 10,000 Units | P(Delay)=84.2%)", fontsize=9, color='#94A3B8', fontfamily='sans-serif')
    
    # Prescription Options
    opt_boxes = [
        ("Plan A: Air Expedite Priority", "Cost: $18,400\nTransit: 2 Days\nSLA Compliance: 99.2%\nPenalty Averted: $85,000", "#10B981", 0.5, 2.5, 2.8, 2.3),
        ("Plan B: Dual Fab Split Route", "Cost: $12,200\nTransit: 4 Days\nSLA Compliance: 91.0%\nPenalty Averted: $60,000", "#38BDF8", 3.6, 2.5, 2.8, 2.3),
        ("Plan C: Buffer Stock Drawdown", "Cost: $6,500\nTransit: 1 Day\nSLA Compliance: 98.5%\nBuffer Left: 18%", "#F59E0B", 6.7, 2.5, 2.8, 2.3)
    ]
    for opt_title, opt_desc, col, x, y, w, h in opt_boxes:
        box = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1", fc='#1E293B', ec=col, lw=2)
        ax.add_patch(box)
        ax.text(x + w/2, y + 1.9, opt_title, fontsize=9.5, fontweight='bold', color=col, ha='center', fontfamily='sans-serif')
        ax.text(x + 0.2, y + 0.4, opt_desc, fontsize=8.5, color='#F8FAFC', fontfamily='sans-serif')
        
    # Solver execution summary box
    solv = patches.Rectangle((0.5, 0.5), 9.0, 1.6, fc='#1E293B', ec='#475569', lw=1.5)
    ax.add_patch(solv)
    ax.text(0.8, 1.8, "Solver Optimization Diagnostics (CBC Solver / PuLP)", fontsize=9.5, fontweight='bold', color='#F8FAFC', fontfamily='sans-serif')
    ax.text(0.8, 1.4, "Status: OPTIMAL  |  Execution Latency: 38.4 ms  |  Variables: 18 (Binary: 6, Continuous: 12)  |  Constraints: 14", fontsize=8, color='#38BDF8', fontfamily='sans-serif')
    ax.text(0.8, 1.0, "Selected Prescription: Plan A (Air Expedite Priority) + Buffer Top-Up from Regional Depot", fontsize=8.5, fontweight='bold', color='#10B981', fontfamily='sans-serif')
    ax.text(0.8, 0.7, "Budget Constraint: $25,000 Cap  -->  Optimal Objective Solution: $18,400 Total Cost", fontsize=8, color='#94A3B8', fontfamily='sans-serif')

    plt.tight_layout()
    plt.savefig('scratch_report_assets/screenshot_optimization.png', dpi=200, bbox_inches='tight')
    plt.close()
    print("Generated all screenshot mockups.")

if __name__ == '__main__':
    generate_flowchart()
    generate_dfd()
    generate_er()
    generate_screenshots()
