import os

def add_chapter_3(doc, h):
    h['add_chapter_cover']("SYSTEM DESIGN")
    h['add_chapter_title']("3. SYSTEM DESIGN")
    
    # 3.1 System Perspective
    h['add_heading_14']("3.1 SYSTEM PERSPECTIVE")
    h['add_body'](
        "SupplyPrescript is engineered as a decoupled, multi-tier enterprise decision-support architecture. The design rigorously adheres to "
        "separation-of-concerns principles, ensuring that data presentation, business optimization logic, and database persistence can evolve, "
        "scale, and be maintained independently. The overall system perspective is organized into three primary operational tiers:"
    )
    
    h['add_heading_12']("3.1.1 User Interface (UI) Presentation Tier")
    h['add_body'](
        "The presentation tier comprises native HTML5, modern CSS3, and vanilla JavaScript client applications running within standard web browsers. "
        "The client layer is partitioned into specialized views: (1) an operations command center for logistics analysts (frontend/index.html) featuring "
        "real-time shipment ingestion, interactive delay risk probability gauges, and dynamic prescriptive optimization controls; (2) an enterprise "
        "authentication portal (frontend/login.html) supporting dual OAuth 2.0 social sign-on (Google and Facebook) alongside local credential sign-in; "
        "and (3) an administrative governance console (frontend/admin.html) for user provisioning, role assignments, and audit trail inspection. "
        "The frontend communicates with the application tier exclusively via asynchronous RESTful HTTP/JSON calls."
    )
    
    h['add_heading_12']("3.1.2 Application Core Logic Tier")
    h['add_body'](
        "The core logic tier is hosted on the high-performance FastAPI asynchronous framework running on Uvicorn. This tier encapsulates:"
    )
    h['add_bullet']("REST API Routing & Security Middleware: Enforces CORS policies, rate limiting, and route protection via JWT session tokens.")
    h['add_bullet']("Pydantic Validation Layer: Enforces strict data contracts on all incoming and outgoing JSON payloads, guaranteeing type safety.")
    h['add_bullet']("Machine Learning Inference Subsystem: Loads pre-trained scikit-learn transformers and XGBoost models to compute delay probabilities.")
    h['add_bullet']("Prescriptive Optimization Engine: Formulates Mixed-Integer Linear Programming models in PuLP and invokes the COIN-OR CBC solver.")
    h['add_bullet']("Identity & OAuth Manager: Handles OAuth 2.0 PKCE state verification, token exchange, and PBKDF2-SHA256 password hashing.")
    
    h['add_heading_12']("3.1.3 Data Persistence Architecture")
    h['add_body'](
        "The data persistence tier utilizes a normalized SQLite 3 database operating in Write-Ahead Logging (WAL) mode with strict foreign key integrity "
        "(PRAGMA foreign_keys = ON). The database maintains seven relational tables tracking shipments, predictions, optimization decisions, outcomes, "
        "users, sessions, and password resets. All transactional operations are wrapped in atomic commit blocks to prevent partial writes."
    )
    
    # 3.2 Input Design
    h['add_heading_14']("3.2 INPUT DESIGN")
    h['add_body'](
        "Input design focuses on ensuring data integrity, minimizing operator entry errors, and facilitating automated programmatic ingestion from "
        "carrier EDI feeds. Key input schemas enforced by Pydantic models in backend/schemas.py include:"
    )
    
    h['add_body']("1. Ingest Shipment Manifest Payload (ShipmentRequest):")
    h['add_bullet']("shipment_id (string, required): Unique alphanumeric consignment tracking identifier (e.g., 'SHP-88219').")
    h['add_bullet']("supplier_name (string, default 'Primary Microchip Fab'): Originating fabrication entity.")
    h['add_bullet']("component (string, default 'Microchips'): Component classification identifier.")
    h['add_bullet']("quantity (integer, > 0): Batch size in units (e.g., 5,000 microchips).")
    h['add_bullet']("scheduled_days (integer, > 0): Carrier baseline transit lead time.")
    h['add_bullet']("shipping_mode, customer_segment, market, order_region, order_country: Logistics routing features.")
    
    h['add_body']("2. Prescriptive Optimization Request Payload (PrescribeRequest):")
    h['add_bullet']("budget (float, >= 0): Maximum allowable emergency mitigation expenditure in USD.")
    h['add_bullet']("max_delivery_days (integer, > 0): Strict contractual service level agreement (SLA) deadline.")
    h['add_bullet']("required_quantity (integer, > 0): Total microchip units required by receiving assembly facility.")
    h['add_bullet']("supplier_capacity (integer, > 0): Available production and freight capacity of target suppliers.")
    h['add_bullet']("options (dictionary, optional): User-defined custom mitigation alternatives specifying individual costs and lead times.")
    
    h['add_body']("3. Manager Decision Governance Payload (ManagerDecisionRequest):")
    h['add_bullet']("decision (string, required): Manager action flag ('APPROVED', 'REJECTED', 'OVERRIDDEN').")
    h['add_bullet']("notes (string, optional): Explanatory managerial commentary and justification.")
    
    h['add_body']("4. Post-Delivery Outcome Payload (OutcomeEvaluationRequest):")
    h['add_bullet']("actual_delivery_days (integer, >= 0): Realized physical transit lead time.")
    h['add_bullet']("actual_cost (float, >= 0): Realized landed freight and mitigation expenditure in USD.")
    h['add_bullet']("delay_occurred (boolean): Indicator whether final arrival exceeded scheduled deadline.")
    h['add_bullet']("decision_effective (boolean): Assessment whether prescribed mitigation achieved its objective.")
    h['add_bullet']("feedback_notes (string, optional): Operator qualitative observations.")
    
    # 3.3 Output Design
    h['add_heading_14']("3.3 OUTPUT DESIGN")
    h['add_body'](
        "Output design emphasizes actionable clarity, visual hierarchy, and immediate operational utility. Primary system outputs encompass:"
    )
    h['add_bullet'](
        "Machine Learning Prediction Response: Returns the target shipment_id, the calibrated delay_probability (rounded to 2 decimal places), "
        "and the projected predicted_delay_days, accompanied by an intuitive visual risk badge (Low, Moderate, High, Severe)."
    )
    h['add_bullet'](
        "Prescriptive Decision Matrix Card: Details the recommended_action (e.g., 'Air Freight'), solver status ('Optimal' or 'Infeasible'), "
        "exact projected expenditure, delivery duration in days, and an exhaustive breakdown of all evaluated alternative options."
    )
    h['add_bullet'](
        "Enterprise Analytics KPI Summary: An aggregated dashboard payload providing total monitored shipments, count of high-risk consignments, "
        "active prescriptions awaiting approval, cumulative mitigation expenditures, and realized disruption savings."
    )
    
    # 3.4 Database Design
    h['add_heading_14']("3.4 DATABASE DESIGN")
    h['add_heading_12']("3.4.1 NORMALIZATION")
    h['add_body'](
        "To prevent insertion, update, and deletion anomalies, minimize data redundancy, and ensure referential integrity, the SupplyPrescript database "
        "was systematically decomposed following Boyce-Codd Normal Form (3NF / BCNF) principles:"
    )
    h['add_bullet'](
        "First Normal Form (1NF): All attributes contain strictly atomic, scalar values. Repeating groups, comma-separated lists, and multi-valued fields "
        "have been eliminated. Each table possesses a designated primary key."
    )
    h['add_bullet'](
        "Second Normal Form (2NF): The schema satisfies 1NF, and every non-key column is fully functionally dependent on the entire primary key, "
        "eliminating partial functional dependencies on composite keys."
    )
    h['add_bullet'](
        "Third Normal Form (3NF): The schema satisfies 2NF, and no non-key attribute is transitively dependent on the primary key. For example, "
        "user authentication credentials, carrier shipment records, predictive model scores, optimization decisions, and post-delivery outcomes "
        "are segregated into distinct relation tables linked via foreign key constraints."
    )
    
    h['add_heading_12']("3.4.2 TABLE STRUCTURE")
    h['add_body']("The physical database schema comprises seven normalized tables in database/supplyprescript.db:")
    
    # Table 3.1: shipments
    h['add_body']("Table 3.1: Table Name - shipments")
    h['add_body']("Description: Stores baseline microchip shipment telemetry, routing attributes, and carrier schedules.")
    table_shipments = [
        ["Field Name", "Data Type", "Constraint", "Description"],
        ["id", "INTEGER", "Primary Key, Auto", "Internal autoincrement database surrogate key"],
        ["shipment_id", "TEXT", "Unique, Not Null", "Unique alphanumeric enterprise tracking identifier"],
        ["supplier_name", "TEXT", "Default 'Primary Fab'", "Originating semiconductor fabrication facility"],
        ["component", "TEXT", "Default 'Microchips'", "Semiconductor device classification identifier"],
        ["quantity", "INTEGER", "Default 5000", "Batch volume in units"],
        ["scheduled_days", "INTEGER", "Default 4", "Baseline carrier scheduled transit days"],
        ["shipping_mode", "TEXT", "Default 'Standard Class'", "Freight service level tier"],
        ["customer_segment", "TEXT", "Default 'Corporate'", "Purchasing organizational category"],
        ["market", "TEXT", "Default 'Pacific Asia'", "Global commercial logistics market"],
        ["order_region", "TEXT", "Default 'Southeast Asia'", "Geographic sector of destination hub"],
        ["order_country", "TEXT", "Default 'Taiwan'", "Sovereign jurisdiction of destination plant"],
        ["created_at", "TIMESTAMP", "Default CURRENT_TIMESTAMP", "Record ingestion UTC timestamp"]
    ]
    h['format_custom_table'](table_shipments, [1.4, 1.1, 1.4, 2.7], is_compact=True)
    
    # Table 3.2: predictions
    h['add_body']("Table 3.2: Table Name - predictions")
    h['add_body']("Description: Stores pre-transit XGBoost delay risk classification probabilities and duration estimates.")
    table_predictions = [
        ["Field Name", "Data Type", "Constraint", "Description"],
        ["id", "INTEGER", "Primary Key, Auto", "Internal autoincrement primary key"],
        ["shipment_id", "TEXT", "Foreign Key, Not Null", "References shipments(shipment_id)"],
        ["delay_probability", "REAL", "Not Null", "Calibrated probability of transit delay in range [0.0, 1.0]"],
        ["predicted_delay_days", "INTEGER", "Not Null", "Projected delay duration in days from XGBoost regressor"],
        ["model_name", "TEXT", "Default 'XGBoost'", "Active predictive model version string"],
        ["created_at", "TIMESTAMP", "Default CURRENT_TIMESTAMP", "Inference execution timestamp"]
    ]
    h['format_custom_table'](table_predictions, [1.4, 1.1, 1.4, 2.7], is_compact=True)
    
    # Table 3.3: optimization_decisions
    h['add_body']("Table 3.3: Table Name - optimization_decisions")
    h['add_body']("Description: Stores PuLP Mixed-Integer Linear Programming decisions, evaluated options, and manager actions.")
    table_decisions = [
        ["Field Name", "Data Type", "Constraint", "Description"],
        ["id", "INTEGER", "Primary Key, Auto", "Internal autoincrement primary key"],
        ["shipment_id", "TEXT", "Foreign Key, Not Null", "References shipments(shipment_id)"],
        ["budget", "REAL", "Not Null", "Enterprise mitigation cost ceiling in USD"],
        ["max_delivery_days", "INTEGER", "Not Null", "Contractual maximum transit SLA deadline"],
        ["required_quantity", "INTEGER", "Not Null", "Component quantity demanded by manufacturing plant"],
        ["supplier_capacity", "INTEGER", "Not Null", "Available supplier inventory and logistics capacity"],
        ["recommended_action", "TEXT", "Nullable", "Optimal prescribed action ('Air Freight', 'Secondary Supplier', etc.)"],
        ["optimization_status", "TEXT", "Not Null", "PuLP solver termination status ('Optimal', 'Infeasible')"],
        ["options_evaluated", "TEXT", "Nullable", "JSON serialized dictionary of all alternatives evaluated by solver"],
        ["manager_decision", "TEXT", "Nullable", "Manager governance action ('APPROVED', 'OVERRIDDEN')"],
        ["notes", "TEXT", "Nullable", "Manager justification and operational remarks"],
        ["created_at", "TIMESTAMP", "Default CURRENT_TIMESTAMP", "Optimization solve timestamp"]
    ]
    h['format_custom_table'](table_decisions, [1.4, 1.1, 1.4, 2.7], is_compact=True)
    
    # Table 3.4: outcomes
    h['add_body']("Table 3.4: Table Name - outcomes")
    h['add_body']("Description: Records realized delivery performance, actual landed costs, and closed-loop feedback variance.")
    table_outcomes = [
        ["Field Name", "Data Type", "Constraint", "Description"],
        ["id", "INTEGER", "Primary Key, Auto", "Internal autoincrement primary key"],
        ["shipment_id", "TEXT", "Foreign Key, Not Null", "References shipments(shipment_id)"],
        ["actual_delivery_days", "INTEGER", "Nullable", "Realized physical transit duration from origin to plant"],
        ["actual_cost", "REAL", "Nullable", "Realized landed freight and mitigation expenditure in USD"],
        ["delay_occurred", "INTEGER", "Default 0", "Binary flag indicating whether physical delay materialized (1=Yes, 0=No)"],
        ["decision_effective", "INTEGER", "Default 1", "Binary flag indicating whether prescribed action averted disruption"],
        ["feedback_notes", "TEXT", "Nullable", "Operator qualitative feedback and root-cause notes"],
        ["recorded_at", "TIMESTAMP", "Default CURRENT_TIMESTAMP", "Outcome evaluation logging timestamp"]
    ]
    h['format_custom_table'](table_outcomes, [1.4, 1.1, 1.4, 2.7], is_compact=True)
    
    # Table 3.5: users
    h['add_body']("Table 3.5: Table Name - users")
    h['add_body']("Description: Stores registered enterprise accounts, RBAC authorization roles, and OAuth provider mappings.")
    table_users = [
        ["Field Name", "Data Type", "Constraint", "Description"],
        ["id", "INTEGER", "Primary Key, Auto", "Unique user primary key identifier"],
        ["username", "TEXT", "Unique, Not Null", "Unique corporate login username"],
        ["email", "TEXT", "Unique, Not Null", "Verified corporate email address"],
        ["password_hash", "TEXT", "Not Null", "PBKDF2-HMAC-SHA256 password hash (100k iterations)"],
        ["salt", "TEXT", "Not Null", "Cryptographically random 16-byte hexadecimal salt"],
        ["role", "TEXT", "Default 'analyst'", "RBAC authorization tier: 'admin', 'manager', 'analyst'"],
        ["full_name", "TEXT", "Nullable", "Full legal name of operator"],
        ["is_active", "INTEGER", "Default 1", "Account operational status flag (1=Active, 0=Disabled)"],
        ["auth_provider", "TEXT", "Default 'local'", "Authentication source: 'local', 'google', 'facebook'"],
        ["facebook_id", "TEXT", "Nullable", "Verified Facebook Graph API user identifier"],
        ["google_id", "TEXT", "Nullable", "Verified Google Identity user identifier"],
        ["created_at", "TIMESTAMP", "Default CURRENT_TIMESTAMP", "Account provisioning timestamp"],
        ["last_login", "TIMESTAMP", "Nullable", "Most recent successful login timestamp"]
    ]
    h['format_custom_table'](table_users, [1.4, 1.1, 1.4, 2.7], is_compact=True)
    
    # Table 3.6: sessions
    h['add_body']("Table 3.6: Table Name - sessions")
    h['add_body']("Description: Manages server-side session tokens with instantaneous cryptographic revocation capabilities.")
    table_sessions = [
        ["Field Name", "Data Type", "Constraint", "Description"],
        ["id", "INTEGER", "Primary Key, Auto", "Internal autoincrement primary key"],
        ["user_id", "INTEGER", "Foreign Key, Not Null", "References users(id) ON DELETE CASCADE"],
        ["session_token", "TEXT", "Unique, Not Null", "Cryptographically random 32-byte session token"],
        ["created_at", "TIMESTAMP", "Default CURRENT_TIMESTAMP", "Session establishment timestamp"],
        ["expires_at", "TIMESTAMP", "Not Null", "Session expiration timestamp (UTC)"],
        ["is_active", "INTEGER", "Default 1", "Session validity status (1=Active, 0=Revoked)"]
    ]
    h['format_custom_table'](table_sessions, [1.4, 1.1, 1.4, 2.7], is_compact=True)
    
    # Table 3.7: password_resets
    h['add_body']("Table 3.7: Table Name - password_resets")
    h['add_body']("Description: Manages cryptographically hashed single-use password reset tokens with time-limited validity.")
    table_resets = [
        ["Field Name", "Data Type", "Constraint", "Description"],
        ["id", "INTEGER", "Primary Key, Auto", "Internal autoincrement primary key"],
        ["user_id", "INTEGER", "Foreign Key, Not Null", "References users(id) ON DELETE CASCADE"],
        ["token_hash", "TEXT", "Unique, Not Null", "SHA-256 hash of single-use reset token"],
        ["created_at", "TIMESTAMP", "Default CURRENT_TIMESTAMP", "Reset token generation timestamp"],
        ["expires_at", "TIMESTAMP", "Not Null", "Token expiration timestamp (1-hour validity window)"],
        ["used", "INTEGER", "Default 0", "Single-use flag ensuring token cannot be replayed"]
    ]
    h['format_custom_table'](table_resets, [1.4, 1.1, 1.4, 2.7], is_compact=True)
    
    # Process Design & PuLP MILP Mathematical Formulation
    h['add_heading_14']("PROCESS DESIGN")
    h['add_heading_12']("Mixed-Integer Linear Programming (MILP) Formulation")
    h['add_body'](
        "The core prescriptive engine in backend/optimization.py formulates a Mixed-Integer Linear Programming model to determine the optimal "
        "disruption mitigation decision. Let O denote the set of available mitigation alternatives (e.g., O = {Air Freight, Secondary Supplier, "
        "Accept Delay, ...}). For each alternative i in O, let C_i denote its financial cost in USD, and let D_i denote its delivery lead time in days. "
        "Let B represent the enterprise budget cost ceiling, T_max represent the maximum delivery SLA deadline, Q_req represent the required component "
        "quantity, and K_supp represent the total available supplier capacity."
    )
    h['add_body'](
        "Decision Variables: Define binary decision variables x_i in {0, 1} for each alternative i in O, where x_i = 1 if alternative i is selected, "
        "and x_i = 0 otherwise."
    )
    h['add_body']("Objective Function: Minimize total disruption mitigation expenditure:")
    h['add_body']("Minimize: Z = sum_{i in O} (x_i * C_i)")
    h['add_body']("Subject to the following operational constraints:")
    h['add_body']("1. Exclusivity Constraint: Exactly one mitigation alternative must be selected:")
    h['add_body']("   sum_{i in O} x_i = 1")
    h['add_body']("2. Budget Constraint: Total mitigation expenditure cannot exceed the enterprise cost ceiling budget B:")
    h['add_body']("   sum_{i in O} (x_i * C_i) <= B")
    h['add_body']("3. SLA Lead Time Constraint: The delivery duration of the chosen action cannot violate maximum SLA deadline T_max:")
    h['add_body']("   sum_{i in O} (x_i * D_i) <= T_max")
    h['add_body']("4. Supplier Capacity Feasibility: The required batch quantity cannot exceed supplier capacity:")
    h['add_body']("   Q_req <= K_supp")
    h['add_body']("5. Integrality: x_i in {0, 1} for all i in O.")
    
    h['add_body'](
        "Standard Mitigation Alternatives: The system initializes with three default baseline alternatives: (1) 'Air Freight' (Cost = $15,000, "
        "Delivery Days = 2); (2) 'Secondary Supplier' (Cost = $18,000, Delivery Days = 4); and (3) 'Accept Delay' (Cost = $0, Delivery Days = "
        "predicted_delay_days). Operators may also inject custom alternatives dynamically via the API payload."
    )
    
    h['add_heading_12']("Algorithmic Resolution via COIN-OR CBC Branch-and-Cut Solver")
    h['add_body'](
        "The mathematical optimization formulation is resolved by the COIN-OR Branch and Cut (CBC) engine invoked through PuLP's PULP_CBC_CMD "
        "interface. The solver executes a multi-phase algorithmic procedure:"
    )
    h['add_body'](
        "1. Linear Programming Relaxation: The integrality constraints x_i in {0, 1} are initially relaxed to continuous bounds 0 <= x_i <= 1. "
        "The resulting linear program (LP) is resolved via the Dual Simplex algorithm, establishing a mathematical lower bound Z_LB on the optimal objective."
    )
    h['add_body'](
        "2. Cutting Plane Generation: If the relaxed solution yields fractional decision variables (e.g., x_1 = 0.6, x_2 = 0.4), Gomory Mixed-Integer "
        "Cuts and knapsack cover cuts are dynamically derived from the simplex tableau. These cuts slice away non-integer polyhedral space without "
        "eliminating any feasible binary solutions, tightening the convex hull."
    )
    h['add_body'](
        "3. Branch and Bound Tree Search: When fractional values persist, the solver branches on the most fractional variable x_k, creating two child "
        "sub-problems: (Child 1: x_k = 0) and (Child 2: x_k = 1). Each node is evaluated using primal heuristics to identify integer feasible solutions, "
        "updating the best known upper bound Z_UB."
    )
    h['add_body'](
        "4. Fathoming and Pruning: Sub-problem branches are pruned (fathomed) under three conditions: (a) Infeasibility—the sub-problem violates budget "
        "or SLA constraints; (b) Bound Sub-optimality—the LP relaxation lower bound exceeds the current best upper bound (Z_LB >= Z_UB); or (c) Integer "
        "Feasibility—all decision variables evaluate to integer values. The algorithm terminates when the optimality gap (Z_UB - Z_LB) / Z_UB falls below "
        "1e-5, guaranteeing proven global optimality."
    )
    
    # 3.5.1 DFD
    h['add_heading_12']("3.5.1 DATA FLOW DIAGRAM")
    h['add_body'](
        "A Data Flow Diagram (DFD) graphically models the boundaries, processes, data stores, and external entities governing information transit "
        "throughout SupplyPrescript."
    )
    h['add_body']("Rules for Constructing a Data Flow Diagram:")
    h['add_bullet']("Data Conservation: Data cannot originate spontaneously; it must flow from an external entity or data store.")
    h['add_bullet']("Process Transformation: Every process must possess both at least one incoming data flow and at least one outgoing data flow.")
    h['add_bullet']("Entity Decoupling: External entities cannot directly query or update internal data stores without traversing an intermediate process.")
    
    h['add_body']("Basic Data Flow Diagram Symbols:")
    h['add_bullet']("External Entity: Represented by a rectangle, signifying external originators or recipients of data (Carrier EDI, Analyst, Manager).")
    h['add_bullet']("Process: Represented by a circle or rounded rectangle, signifying an algorithmic transformation of data (ML Inference, MILP Solve).")
    h['add_bullet']("Data Store: Represented by parallel horizontal open lines, signifying persistent database tables.")
    h['add_bullet']("Data Flow: Represented by directed arrows, indicating the direction of information transit.")
    
    h['add_body'](
        "Context Diagram (Level 0 DFD): Figure 3.1 depicts the high-level Level 0 Context Diagram of SupplyPrescript, capturing external entity "
        "interactions with the central analytical system core."
    )
    
    dfd_path = os.path.join(r"C:\Academic Project\Supply-Prescript\scratch_report_assets", "dfd_context.png")
    h['add_image_figure'](dfd_path, "Figure 3.1: SupplyPrescript Level 0 Context Data Flow Diagram", width_inches=6.0)
    
    h['add_body']("Level 1 Data Flow Diagram (Functional Process Decomposition):")
    h['add_body'](
        "The Level 1 DFD decomposes central Process 0.0 into five interconnected functional sub-processes, establishing clear boundaries of data exchange:"
    )
    h['add_bullet']("Process 1.0 (Shipment Ingestion & Validation): Ingests carrier EDI telemetry, validates schema attributes via Pydantic, and writes records to the 'shipments' data store.")
    h['add_bullet']("Process 2.0 (Pre-Transit Machine Learning Inference): Extracts 13 approved features, invokes XGBoost models, computes P(Delay) and predicted delay days, and persists records to 'predictions'.")
    h['add_bullet']("Process 3.0 (Mixed-Integer Linear Prescriptive Optimization): Evaluates budget ceilings, SLA deadlines, and supplier capacities via PuLP MILP, writing candidate plans to 'optimization_decisions'.")
    h['add_bullet']("Process 4.0 (Managerial Governance & Authorization): Presents recommended actions to supply chain managers, receives approval or override decisions, and updates governance audit flags.")
    h['add_bullet']("Process 5.0 (Post-Delivery Outcome Feedback): Captures actual arrival dates and landed expenditures from logistics analysts, calculating variance and persisting records to 'outcomes'.")
    
    h['add_body']("Level 2 Data Flow Diagram (Process 3.0 Prescriptive Optimization Sub-system):")
    h['add_body'](
        "Process 3.0 is further partitioned into fine-grained sub-processes: (3.1) Options Dictionary Resolution (merges default Air Freight and Secondary Supplier alternatives with dynamic custom inputs); (3.2) Supplier Capacity Feasibility Check (evaluates whether required quantity exceeds supplier capacity bounds); (3.3) Objective Function Assembly (generates linear cost sum); (3.4) Constraint Generation (attaches budget and SLA inequalities); (3.5) COIN-OR CBC Solver Invocation; and (3.6) Solution Parsing and Infeasibility Handling."
    )
    
    # 3.5.2 ER Diagram
    h['add_heading_12']("3.5.2 ENTITY-RELATIONSHIP DIAGRAM")
    h['add_body'](
        "The Entity-Relationship (ER) model formalizes the logical conceptual structure of the database. The foundational ER components are:"
    )
    h['add_bullet']("Entity: A distinct real-world object or concept possessing independent existence (e.g., USERS, SHIPMENTS, PREDICTIONS).")
    h['add_bullet']("Relationship: An association among two or more entities (e.g., SHIPMENTS 'receives' PREDICTIONS).")
    h['add_bullet']("Binary Relationship: An association involving exactly two entity types.")
    h['add_bullet']("Recursive Relationship: An association where the same entity participates more than once in distinct roles.")
    h['add_bullet']("Attribute: A descriptive property or characteristic of an entity (e.g., delay_probability, budget).")
    h['add_bullet']("Cardinality & Modality: Specifies the minimum and maximum occurrences of entity participation (1:1, 1:M, M:N).")
    
    h['add_body'](
        "Figure 3.2 depicts the complete Entity-Relationship Diagram for SupplyPrescript, detailing entities, primary keys, foreign key references, "
        "and cardinalities across shipments, predictions, decisions, outcomes, and users."
    )
    
    er_path = os.path.join(r"C:\Academic Project\Supply-Prescript\scratch_report_assets", "er_diagram.png")
    h['add_image_figure'](er_path, "Figure 3.2: SupplyPrescript Entity-Relationship (ER) Diagram", width_inches=6.0)
    
    doc.add_page_break()
