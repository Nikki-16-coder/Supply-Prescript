def add_chapter_1(doc, h):
    # h is a dict of helper functions:
    # add_chapter_cover, add_chapter_title, add_heading_14, add_heading_12,
    # add_body, add_bullet, add_code_block, add_image_figure, format_custom_table
    
    h['add_chapter_cover']("1.INTRODUCTION")
    h['add_chapter_title']("1. INTRODUCTION")
    h['add_heading_14']("PROJECT DESCRIPTION")
    
    h['add_body'](
        "Modern industrial manufacturing, high-performance computing, consumer electronics, and automotive engineering "
        "are underpinned by an intricate, highly specialized, and globally interdependent semiconductor supply chain. "
        "Advanced microprocessors, microcontrollers (MCUs), power management integrated circuits (PMICs), and application-specific "
        "integrated circuits (ASICs) represent the indispensable nervous system of contemporary infrastructure. However, the physical "
        "realities of semiconductor fabrication render this supply network uniquely fragile and susceptible to severe operational "
        "disruptions. A modern semiconductor device requires up to a thousand specialized processing steps spanning three to five months "
        "of front-end wafer fabrication in high-purity ISO Class 1 cleanrooms, followed by intricate back-end assembly, packaging, and "
        "testing (OSAT) across geographically dispersed overseas facilities."
    )
    
    h['add_body'](
        "Geographically, the front-end fabrication of leading-edge sub-7-nanometer microchips is concentrated within a narrow geographic corridor "
        "in East Asia, primarily Taiwan, South Korea, and Japan. Once raw silicon wafers complete lithographic patterning, etching, and chemical "
        "mechanical planarization, they undergo dicing and encapsulation in packaging facilities distributed across Southeast Asia (e.g., Malaysia, "
        "Vietnam, and the Philippines) before being routed to final tier-1 subsystem manufacturers and automotive assembly plants across North America, "
        "Europe, and worldwide markets. This multi-echelon transit journey relies upon multi-modal freight corridors encompassing oceanic container "
        "vessels, bonded cross-border customs gateways, regional transshipment hubs, and scheduled transcontinental air cargo."
    )
    
    h['add_body'](
        "Because automotive and aerospace assembly plants operate under strict Just-In-Time (JIT) and Just-In-Sequence (JIS) production paradigms, "
        "buffer inventories of critical microchips are intentionally minimized to reduce capital holding costs. Consequently, even a minor delay in "
        "the arrival of a single consignment of low-cost microcontrollers can precipitate the complete shutdown of a billion-dollar automotive assembly "
        "line. As demonstrated during recent global supply shocks, maritime port congestion, geopolitical export restrictions, regional airspace "
        "closures, and sudden fabrication maintenance downtimes regularly generate cascading disruption waves that inflict catastrophic financial "
        "losses. Automotive original equipment manufacturers (OEMs) have sustained tens of billions of dollars in lost vehicle output, idle factory "
        "wages, and contractual delivery penalties directly traceable to delayed semiconductor shipments."
    )
    
    h['add_body'](
        "Historically, enterprise logistics operations have managed supply chain volatility through reactive, fragmented, and human-dependent "
        "mechanisms. Traditional transport management systems (TMS) and enterprise resource planning (ERP) suites rely on post-departure "
        "electronic data interchange (EDI) milestone updates. Disruption warnings are triggered only after a carrier vessel has physically failed "
        "to arrive at an intermediate port or after a missed transit milestone has already occurred. By the time a disruption alert surfaces on a "
        "logistics dashboard, the shipment is already stranded in transit, leaving coordinators with a rapidly diminishing window of viable "
        "countermeasures."
    )
    
    h['add_body'](
        "Furthermore, traditional disruption recovery is characterized by heuristic, ad-hoc decision-making under high psychological pressure. "
        "When an unexpected delay threat emerges, logistics coordinators frequently resort to emergency air freight expediting on an instinctual "
        "basis, incurring exorbitant spot freight surcharges. In many instances, emergency air freight is booked needlessly when localized factory "
        "buffer stock could have safely absorbed the transit slippage at negligible expense. Conversely, coordinators sometimes choose to wait out a "
        "minor delay, failing to anticipate that factory buffer inventory will deplete prematurely, culminating in catastrophic factory line downtime. "
        "The lack of mathematical prescriptive optimization leads to chronic budget blowouts, inefficient resource utilization, and uncoordinated "
        "procurement responses."
    )
    
    h['add_body'](
        "SupplyPrescript is an advanced enterprise decision-intelligence platform engineered to fundamentally resolve the limitations of traditional "
        "disruption management. Operating at the confluence of predictive machine learning and prescriptive mathematical optimization, SupplyPrescript "
        "replaces reactive operational fire-fighting with proactive, pre-transit disruption defense. The platform shifts the operational intervention "
        "horizon to the crucial pre-transit phase—the precise window between shipment scheduling and physical carrier handover."
    )
    
    h['add_body'](
        "To establish empirical predictive intelligence, SupplyPrescript incorporates a high-performance machine learning pipeline trained on the "
        "DataCo Supply Chain dataset, comprising over 180,000 historical global commercial freight transactions. Trained on 13 rigorously curated, "
        "non-leaking logistics features, the system's Extreme Gradient Boosting (XGBoost) classifier predicts delay probability prior to shipment "
        "dispatch with an empirical precision of 84.31% and an ROC-AUC of 73.70%. A paired XGBoost regression model forecasts the exact projected "
        "delay duration in days (Mean Absolute Error of 0.48 days), providing quantitative risk intelligence."
    )
    
    h['add_body'](
        "Crucially, SupplyPrescript does not stop at predictive risk scoring. Passive risk heatmaps provide little utility without actionable, "
        "cost-bounded guidance. The core innovation of SupplyPrescript is its closed-loop prescriptive engine, formulated as a Mixed-Integer "
        "Linear Programming (MILP) model using the PuLP framework and solved via the industrial-grade COIN-OR Branch and Cut (CBC) mathematical solver. "
        "When a pre-transit shipment is classified as disruption-prone, the prescriptive engine synthesizes delay duration, contractual service level "
        "agreements (SLAs), air freight expediting costs, secondary fab production surcharges, and inventory holding penalties to compute the mathematically "
        "optimal recovery action."
    )
    
    h['add_body'](
        "Every prescriptive recommendation generated by SupplyPrescript is strictly constrained by user-defined enterprise cost ceilings and supplier "
        "capacity bounds. If a disruption scenario is mathematically unrecoverable within specified financial or lead-time boundaries, the system "
        "truthfully reports an Infeasible status with root-cause diagnostic feedback, preventing erroneous capital expenditure. Once recommendations "
        "are approved by authorized managerial personnel, decisions are persisted into an immutable relational audit log, establishing an accountable, "
        "governed, and auditable closed-loop decision ecosystem."
    )
    
    h['add_heading_14']("SYSTEM STAKEHOLDERS & USER ROLES")
    h['add_body'](
        "The SupplyPrescript platform is architected around strict Role-Based Access Control (RBAC) principles to mirror enterprise organizational "
        "hierarchies and ensure appropriate separation of duties across logistics operations:"
    )
    
    h['add_bullet'](
        "System Administrator (Admin): Holds global governance privileges over the platform. Administrators are empowered to manage corporate user "
        "accounts, configure Single Sign-On (SSO) OAuth 2.0 identity providers (Google and Facebook), adjust enterprise security parameters, inspect "
        "unalterable system audit logs, and oversee database schema migrations and backups. Administrators ensure the platform operates within "
        "enterprise IT compliance, data privacy, and security mandates."
    )
    h['add_bullet'](
        "Supply Chain Manager (Manager): Serves as the primary operational authority over disruption governance and procurement expenditures. "
        "Managers review automated prescriptive optimization plans generated by the PuLP engine, evaluate side-by-side cost and lead-time trade-offs, "
        "approve or override high-impact mitigation actions (such as authorizing emergency air chartering or secondary fab split orders), adjust "
        "enterprise cost ceiling thresholds, and monitor macro disruption KPIs across international shipping lanes."
    )
    h['add_bullet'](
        "Logistics Analyst (Analyst): Represents the frontline operational user responsible for daily logistics monitoring. Analysts ingest raw shipment "
        "schedules and carrier manifests, execute real-time ML risk predictions, evaluate delay probability curves, conduct ad-hoc simulation scenarios, "
        "and record post-delivery outcome feedback (actual arrival dates and realized costs) to close the analytical learning loop."
    )
    
    h['add_heading_14']("PROJECT SCOPE AND OBJECTIVES")
    h['add_body'](
        "The primary objectives of the SupplyPrescript academic research and engineering development project encompass:"
    )
    h['add_bullet'](
        "Pre-Transit Disruption Forecasting: Formulate, train, and validate a machine learning classification pipeline capable of predicting "
        "semiconductor transit delays prior to physical cargo dispatch, strictly preventing post-transit data leakage."
    )
    h['add_bullet'](
        "Prescriptive Mathematical Optimization: Develop a Mixed-Integer Linear Programming model that formulates and solves disruption mitigation "
        "trade-offs in sub-50-millisecond execution times, adhering strictly to budget ceilings, SLA deadlines, and supplier capacities."
    )
    h['add_bullet'](
        "Closed-Loop Enterprise Governance: Construct an end-to-end web platform integrating secure multi-provider authentication (OAuth 2.0 Google "
        "and Facebook SSO), role-based access control, relational database persistence, and post-delivery outcome variance logging."
    )
    h['add_bullet'](
        "Empirical Validation: Quantitatively validate system accuracy, mathematical convergence, algorithmic execution latency, and economic return on "
        "investment through extensive unit, integration, and security testing suites."
    )
    
    h['add_heading_14']("REPORT STRUCTURE & DOCUMENT ROADMAP")
    h['add_body'](
        "This project report is structured across ten comprehensive chapters adhering to formal academic and institutional documentation guidelines:"
    )
    h['add_bullet']("Chapter 1 (Introduction): Presents the semiconductor manufacturing context, logistics vulnerability, problem statement, user personas, and project objectives.")
    h['add_bullet']("Chapter 2 (System Analysis): Conducts a rigorous comparative analysis of existing vs. proposed systems, feasibility studies, hardware/software technology stack, feature engineering, mathematical derivation of XGBoost, and Software Requirement Specifications.")
    h['add_bullet']("Chapter 3 (System Design): Outlines the multi-tier system perspective, input/output schemas, database normalization, 7 normalized table schemas, PuLP MILP formulation, Branch-and-Cut algorithm, Data Flow Diagrams (Context, Level 1, Level 2), and Entity-Relationship model.")
    h['add_bullet']("Chapter 4 (System Testing): Details testing methodologies, security probing (OWASP, PBKDF2, OAuth state), empirical latency benchmarks, and 16 formal test cases across the test suite.")
    h['add_bullet']("Chapter 5 (System Implementation): Reviews deployment environments, programmer and user training curricula, database conversion runbooks, cutover procedures, and post-implementation audit findings.")
    h['add_bullet']("Chapter 6 (System Maintenance): Details corrective defect handling, adaptive model retraining protocols, operating system patch cycles, and perfective algorithmic optimizations.")
    h['add_bullet']("Chapter 7 (Future Enhancement): Explores advanced roadmaps including satellite IoT wafer telemetry, Graph Neural Networks, deep reinforcement learning, carbon footprint optimization, and smart contract execution.")
    h['add_bullet']("Chapter 8 (Conclusion): Synthesizes research contributions, presents an empirical comparison against legacy operations, details quantitative ROI metrics, and summarizes findings.")
    h['add_bullet']("Chapter 9 (Appendix): Provides production source code listings from core modules and embeds actual screenshots of the running application (Home Page, Login Page, Admin Home Page).")
    h['add_bullet']("Chapter 10 (Bibliography): Contains authoritative scholarly citations spanning supply chain operations research, machine learning, software engineering, and official technical references.")
    
    doc.add_page_break()
