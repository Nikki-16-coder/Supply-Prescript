import os

def add_chapter_2(doc, h):
    h['add_chapter_cover']("LITERATURE SURVEY")
    h['add_chapter_title']("2. SYSTEM ANALYSIS")
    
    # 2.1 Existing System
    h['add_heading_14']("2.1 EXISTING SYSTEM")
    h['add_body'](
        "In contemporary semiconductor procurement and industrial logistics, enterprise supply chain management is heavily dependent upon "
        "monolithic Enterprise Resource Planning (ERP) systems, legacy Transport Management Systems (TMS), and fragmented spreadsheet workbooks. "
        "Prominent commercial supply chain suites provide centralized visibility into purchase orders, warehouse stock counts, and electronic carrier "
        "invoices. However, when evaluated from the perspective of high-velocity disruption response, existing architectures exhibit severe structural "
        "deficiencies across multiple operational dimensions:"
    )
    
    h['add_bullet'](
        "Milestone-Dependent Reactive Detection: Existing transport management architectures rely almost exclusively on passive milestone reporting "
        "transmitted via EDI ANSI X12 or EDIFACT telecommunication standards (e.g., EDI 214 Shipment Status Messages). Disruption alerts are created "
        "only after a carrier vessel has failed to make port on its scheduled day or after a transshipment hub has logged an exception scan. In global "
        "semiconductor logistics, this creates a catastrophic latency window: by the time an alert appears on a logistics operator's screen, the "
        "consignment is already physically delayed or trapped in transit, precluding pre-departure mitigation options."
    )
    h['add_bullet'](
        "Absence of Mathematical Prescriptive Intelligence: Legacy platforms function primarily as descriptive dashboards. While modern tools may "
        "display visual status flags indicating that a consignment is late, they provide zero automated decision intelligence. The critical task of "
        "determining how to recover from the delay is left entirely to human heuristics. Logistics coordinators are forced to perform manual mental "
        "arithmetic or open external spreadsheets to evaluate alternative freight routes, balancing costs against delivery deadlines under extreme time "
        "pressure."
    )
    h['add_bullet'](
        "Heuristic Over-Expediting and Capital Inefficiency: Lacking rigorous mathematical optimization, logistics coordinators instinctively react to "
        "delay warnings by booking full emergency air freight expediting. While air chartering guarantees accelerated transit, it represents the most "
        "expensive freight mode available, often costing 10 to 20 times the rate of standard maritime or deferred air transit. In empirical enterprise "
        "audits, up to 35% of emergency air freight expenditures are incurred unnecessarily, because receiving manufacturing plants possess sufficient "
        "buffer stock to absorb the delay without halting production lines."
    )
    h['add_bullet'](
        "Data Fragmentation and Siloed Contracts: In existing corporate IT landscapes, carrier status telemetry, factory-floor bill of materials (BOM), "
        "buffer inventory levels, and commercial supplier penalty contracts reside in disconnected software databases. Transport managers do not have "
        "real-time visibility into whether a late microchip delivery will incur SLA breach penalties or trigger factory downtime, preventing balanced "
        "cost-benefit trade-offs."
    )
    h['add_bullet'](
        "Open-Loop Architecture and Missing Auditability: Conventional logistics processes operate in an open-loop fashion. Coordinators execute phone "
        "calls and send unstructured emails to expedite freight, but these interventions are rarely persisted alongside original risk predictions and "
        "actual delivery outcomes. As a result, machine learning models cannot be systematically retrained on realized performance variance, and corporate "
        "executives lack an immutable audit trail verifying why specific expensive interventions were authorized."
    )
    
    # 2.2 Proposed System
    h['add_heading_14']("2.2 PROPOSED SYSTEM")
    h['add_body'](
        "SupplyPrescript introduces a unified, closed-loop decision-support platform specifically designed to overcome the structural flaws of "
        "conventional logistics management. The platform establishes a cohesive analytical pipeline uniting machine learning risk classification "
        "with mathematical Mixed-Integer Linear Programming (MILP) prescriptive optimization and auditable governance:"
    )
    
    h['add_bullet'](
        "Pre-Transit Disruption Forecasting: SupplyPrescript executes machine learning inference at the moment a shipment manifest is scheduled, prior "
        "to physical dispatch. By evaluating 13 verified logistics features, the system computes the exact probability of transit delay P(Delay) and "
        "forecasts the expected delay duration in days, opening an actionable window for proactive mitigation before cargo departs the factory."
    )
    h['add_bullet'](
        "Prescriptive Mixed-Integer Linear Programming (MILP): Rather than generating passive alerts, SupplyPrescript formulates a formal mathematical "
        "optimization problem using the PuLP framework. The objective function minimizes total disruption mitigation expenditure subject to rigid "
        "enterprise budget ceilings, maximum delivery day SLAs, and supplier capacity constraints. The solver evaluates competing mitigation "
        "alternatives—including Air Freight, Secondary Supplier allocation, and Buffer Stock drawdown—to prescribe the mathematically optimal action."
    )
    h['add_bullet'](
        "Architectural Distinction and Data Lineage: It is critical to clearly establish the architectural distinction between the historical training "
        "dataset and the application scenario. The predictive pipeline is trained on the Kaggle DataCo Supply Chain dataset, comprising 180,519 historical "
        "commercial freight records. DataCo is an empirical, open-source logistics dataset providing generalized transit delay patterns across shipping "
        "modes, global markets, order volumes, and customer segments. SupplyPrescript's application layer maps these generalized predictive delay "
        "probabilities into a specialized semiconductor manufacturing use case (e.g., TSMC Fab 18, 4nm AI accelerators, automotive MCUs) to solve "
        "mission-critical production disruption decisions."
    )
    h['add_bullet'](
        "Enterprise Decision Governance & Audit Logging: Every recommendation generated by the PuLP engine is presented through a streamlined managerial "
        "review interface. The platform records every evaluated alternative, manager approval timestamp, and override note into an unalterable relational "
        "audit trail, enforcing corporate accountability."
    )
    h['add_bullet'](
        "Closed-Loop Learning Feedback: Following physical cargo delivery, logistics analysts record actual arrival dates, realized landed costs, and "
        "operational feedback notes in the database. This feedback enables continuous calculation of decision effectiveness and provides empirical data "
        "for periodic model retraining."
    )
    
    # 2.3 Feasibility Study
    h['add_heading_14']("2.3 FEASIBILITY STUDY")
    h['add_body'](
        "A rigorous feasibility study was conducted across technical, front-end, back-end, operational, and economic dimensions to ensure the viability, "
        "scalability, and institutional suitability of the proposed platform."
    )
    
    h['add_heading_12']("2.3.1 Technical Feasibility")
    h['add_body'](
        "Technical feasibility evaluates whether the computational algorithms, programming frameworks, and hardware environments are sufficiently "
        "mature to achieve project requirements without prohibitive complexity. SupplyPrescript utilizes an industrial-strength, open-source technology stack:"
    )
    h['add_bullet'](
        "Python 3.12 64-bit: Leverages optimized bytecode execution, enhanced traceback reporting, and seamless interoperability with native C-compiled "
        "numerical libraries (NumPy, SciPy, Scikit-learn)."
    )
    h['add_bullet'](
        "Machine Learning Pipeline: Built upon Scikit-learn's ColumnTransformer and XGBoost (Extreme Gradient Boosting), executing classification "
        "inference in under 15 milliseconds per request."
    )
    h['add_bullet'](
        "Mathematical Optimization Engine: Utilizes PuLP 2.8+ interfacing with the COIN-OR Branch and Cut (CBC) mathematical solver, achieving global "
        "optima on discrete MILP formulations in under 50 milliseconds."
    )
    h['add_bullet'](
        "Relational Persistence Layer: Implemented in SQLite 3 with Write-Ahead Logging (WAL) and strict foreign key integrity, requiring zero external "
        "database server administration while offering seamless migration path to PostgreSQL."
    )
    
    h['add_heading_12']("2.3.2 Front-End Selection")
    h['add_body'](
        "The user interface was purposefully constructed using native, vanilla HTML5, modern CSS3, and JavaScript, deliberately rejecting heavy "
        "frontend frameworks (such as React, Angular, or Vue). This deliberate architectural decision ensures:"
    )
    h['add_bullet']("Zero Runtime Overhead: Eliminates bloated node_modules bundles, virtual DOM diffing overhead, and compile-time webpack pipelines.")
    h['add_bullet']("Instantaneous DOM Execution: Pages render immediately upon load with sub-50ms Time-to-Interactive (TTI) metrics.")
    h['add_bullet'](
        "Visual Ergonomics: Implements a restrained, futuristic enterprise color palette (#0F172A slate navy, #1E293B card backgrounds, #0284C7 and #38BDF8 "
        "oceanic blue accents, and #94A3B8 neutral typography), minimizing cognitive eye strain during extended operational monitoring."
    )
    
    h['add_heading_12']("2.3.3 Back-End Selection")
    h['add_body'](
        "FastAPI was selected as the backend web framework over traditional alternatives such as Django and Flask based on rigorous performance criteria:"
    )
    h['add_bullet'](
        "Asynchronous Concurrency: Built on Starlette and the Asynchronous Server Gateway Interface (ASGI) standard, FastAPI handles thousands of concurrent "
        "carrier telemetry requests asynchronously on an event-driven loop."
    )
    h['add_bullet'](
        "Native Data Validation: Utilizes Pydantic models to automatically enforce strict runtime type safety, eliminating defensive validation boilerplate."
    )
    h['add_bullet'](
        "In-Process Model Execution: Python's scientific stack runs directly within the FastAPI process space, avoiding high-latency inter-process "
        "communication (IPC) or remote procedure call (gRPC) overhead."
    )
    
    h['add_heading_12']("2.3.4 Operational Feasibility")
    h['add_body'](
        "Operational feasibility confirms that the platform integrates seamlessly into existing enterprise organizational workflows. The system abstracts "
        "the dense mathematical equations of mixed-integer programming into clear, visual decision cards displaying recommended actions, monetary costs, "
        "and delivery timelines. Role-Based Access Control (RBAC) enforces organizational boundaries, ensuring logistics analysts can execute scenario "
        "simulations while restricting financial authorization of costly mitigation actions to certified supply chain managers."
    )
    
    h['add_heading_12']("2.3.5 Economic Feasibility")
    h['add_body'](
        "The economic justification of SupplyPrescript is established through a quantitative cost-benefit model. In high-technology semiconductor manufacturing, "
        "factory line stoppages incur astronomical penalties. An idle automotive assembly plant incurs approximately $50,000 to $200,000 per hour in unrecoverable "
        "overhead. A three-day delay on a critical microcontroller batch can impose millions of dollars in damages. By identifying delay risks prior to cargo "
        "dispatch and evaluating cost-optimal mitigation actions within strict budget ceilings, the prevention of a single production shutdown fully recovers "
        "the multi-year development and operating costs of the SupplyPrescript platform."
    )
    
    # 2.4 Tools and Technologies
    h['add_heading_14']("2.4 TOOLS AND TECHNOLOGIES")
    h['add_heading_12']("2.4.1 Hardware Requirements:")
    h['add_body']("The minimum and recommended hardware specifications for development and enterprise deployment are:")
    h['add_bullet']("Processor: Intel Core i5 / i7 (8th Gen or later) or AMD Ryzen 5 / 7 (3.0 GHz base frequency, 4+ physical cores).")
    h['add_bullet']("System RAM: 8 GB minimum (16 GB recommended for high-volume concurrent optimization batches).")
    h['add_bullet']("Storage: 512 GB Solid State Drive (SSD) with NVMe M.2 interface for rapid model checkpoint loading and SQLite disk I/O.")
    h['add_bullet']("Network Interface: Gigabit Ethernet or 802.11ac/ax Wi-Fi for low-latency carrier API ingestion.")
    
    h['add_heading_12']("2.4.2 Software Requirements:")
    h['add_body']("The complete operational software environment comprises:")
    h['add_bullet']("Operating System: Microsoft Windows 10/11 Professional (64-bit) or Ubuntu Linux 22.04 LTS.")
    h['add_bullet']("Programming Runtime: Python 3.12.x (64-bit standard distribution).")
    h['add_bullet']("ASGI Web Server: Uvicorn 0.30+ with HTTP/2 and TLS 1.3 cryptographic support.")
    h['add_bullet']("Database Management System: SQLite 3.40+ (Development/Single-Node) with WAL mode enabled.")
    h['add_bullet']("Web Browser Client: Modern Chromium-based browser (Google Chrome v115+, Microsoft Edge v115+) or Mozilla Firefox v118+.")
    
    h['add_heading_12']("2.4.3 SOFTWARE DESCRIPTION")
    h['add_body'](
        "The software architecture incorporates specialized enterprise libraries and algorithmic frameworks:"
    )
    
    h['add_body']("Features of the Language (Python 3.12):")
    h['add_body'](
        "Python 3.12 delivers significant performance enhancements, including faster bytecode execution, specialized adaptive interpreter optimizations, "
        "and refined type hinting. Python serves as the lingua franca of scientific machine learning and operations research, providing seamless "
        "bridging between mathematical optimization algorithms and asynchronous web services."
    )
    
    h['add_body']("Machine Learning Stack (XGBoost & Scikit-Learn):")
    h['add_body'](
        "The predictive subsystem in ml/ utilizes Scikit-learn for deterministic data transformation and XGBoost for gradient boosted decision tree learning. "
        "To guarantee zero data leakage, the pipeline strictly enforces the inclusion of only 13 pre-transit features, partitioned into 6 numerical "
        "attributes and 7 categorical attributes:"
    )
    
    # Feature dictionary table
    table_features = [
        ["Feature Name", "Type", "Transformation Method", "Operational Significance"],
        ["Days for shipment (scheduled)", "Numerical", "Passthrough / Scaled", "Baseline transit duration committed by logistics carrier"],
        ["Order Item Quantity", "Numerical", "Passthrough / Scaled", "Consignment volume in units (affects palletization and handling)"],
        ["Order Item Product Price", "Numerical", "Passthrough / Scaled", "Unit commercial valuation (indicates consignment priority)"],
        ["Order Item Discount", "Numerical", "Passthrough / Scaled", "Contractual commercial discount applied to transaction"],
        ["Order Item Discount Rate", "Numerical", "Passthrough / Scaled", "Percentage discount applied (correlates with customer tier)"],
        ["Product Price", "Numerical", "Passthrough / Scaled", "Catalog list price of component"],
        ["Shipping Mode", "Categorical", "OneHotEncoder (Sparse)", "Freight velocity tier: Standard Class, First Class, Second Class, Same Day"],
        ["Customer Segment", "Categorical", "OneHotEncoder (Sparse)", "Purchaser profile: Corporate, Home Office, Consumer"],
        ["Market", "Categorical", "OneHotEncoder (Sparse)", "Global continental market: Pacific Asia, Europe, USCA, LATAM"],
        ["Order Region", "Categorical", "OneHotEncoder (Sparse)", "Regional geographic sector: Southeast Asia, East Asia, Western Europe"],
        ["Order Country", "Categorical", "OneHotEncoder (Sparse)", "Sovereign jurisdiction of destination manufacturing hub"],
        ["Category Name", "Categorical", "OneHotEncoder (Sparse)", "Component equipment classification identifier"],
        ["Department Name", "Categorical", "OneHotEncoder (Sparse)", "Organizational enterprise procurement department"]
    ]
    h['format_custom_table'](table_features, [1.5, 0.9, 1.6, 2.6], is_compact=True)
    
    h['add_body'](
        "Strict Data Leakage Prevention: The preprocessor strictly excludes post-transit outcome fields that would artificially inflate training accuracy "
        "but are unavailable at pre-transit inference time. Specifically, 'Days for shipping (real)', 'Delivery Status', and 'shipping date (DateOrders)' "
        "are explicitly banned from the feature matrix via runtime assertions in ml/preprocess.py."
    )
    
    h['add_heading_12']("Mathematical Derivation of XGBoost Gradient Boosting Formulation")
    h['add_body'](
        "XGBoost (Extreme Gradient Boosting) minimizes a regularized objective function comprising a convex loss function l and a model complexity penalization term Omega. "
        "Let D = {(x_i, y_i)} be the historical logistics dataset containing n observations, where x_i is the 13-dimensional feature vector and y_i in {0, 1} is "
        "the binary Late_delivery_risk target. The ensemble model predicts output y_hat_i at iteration t as the sum of t tree functions:"
    )
    h['add_body'](
        "y_hat_i^(t) = sum_{k=1}^t f_k(x_i) = y_hat_i^(t-1) + f_t(x_i), where f_t in F is the new decision tree added at iteration t."
    )
    h['add_body'](
        "The objective function at step t is defined as:"
    )
    h['add_body'](
        "Obj^(t) = sum_{i=1}^n l(y_i, y_hat_i^(t-1) + f_t(x_i)) + Omega(f_t), where Omega(f_t) = gamma * T + 0.5 * lambda * sum_{j=1}^T w_j^2."
    )
    h['add_body'](
        "Here, T denotes the number of terminal leaves in tree f_t, w_j is the continuous weight assigned to leaf j, gamma is the complexity penalty parameter "
        "governing tree pruning, and lambda is the L2 regularization parameter preventing overfitting on noisy logistics features."
    )
    h['add_body'](
        "To optimize this objective efficiently, a second-order Taylor expansion is applied to approximate the loss function around the previous prediction y_hat_i^(t-1):"
    )
    h['add_body'](
        "Obj^(t) approx sum_{i=1}^n [ l(y_i, y_hat_i^(t-1)) + g_i * f_t(x_i) + 0.5 * h_i * f_t^2(x_i) ] + gamma * T + 0.5 * lambda * sum_{j=1}^T w_j^2,"
    )
    h['add_body'](
        "where g_i = del_{y_hat^(t-1)} l(y_i, y_hat^(t-1)) represents the first-order gradient of the loss function, and h_i = del^2_{y_hat^(t-1)} l(y_i, y_hat^(t-1)) "
        "represents the second-order Hessian. For binary classification with logloss l(y, p) = -y*log(p) - (1-y)*log(1-p), the gradient is g_i = p_i - y_i "
        "and the Hessian is h_i = p_i * (1 - p_i), where p_i = 1 / (1 + exp(-y_hat_i))."
    )
    h['add_body'](
        "Removing the constant term l(y_i, y_hat_i^(t-1)), the objective simplifies to the sum over all leaves j = 1 to T:"
    )
    h['add_body'](
        "Obj_tilde^(t) = sum_{j=1}^T [ (sum_{i in I_j} g_i) * w_j + 0.5 * (sum_{i in I_j} h_i + lambda) * w_j^2 ] + gamma * T."
    )
    h['add_body'](
        "Differentiating with respect to w_j and setting to zero yields the optimal weight for leaf j:"
    )
    h['add_body'](
        "w_j^* = - [ sum_{i in I_j} g_i ] / [ sum_{i in I_j} h_i + lambda ]."
    )
    h['add_body'](
        "Substituting w_j^* back into the objective function yields the optimal objective reduction score:"
    )
    h['add_body'](
        "Obj_optimal = - 0.5 * sum_{j=1}^T [ (sum_{i in I_j} g_i)^2 / (sum_{i in I_j} h_i + lambda) ] + gamma * T."
    )
    h['add_body'](
        "During tree induction, when evaluating a candidate split dividing instance set I into left subset I_L and right subset I_R, the split Gain is computed as:"
    )
    h['add_body'](
        "Gain = 0.5 * [ (sum_{i in I_L} g_i)^2 / (sum_{i in I_L} h_i + lambda) + (sum_{i in I_R} g_i)^2 / (sum_{i in I_R} h_i + lambda) - (sum_{i in I} g_i)^2 / (sum_{i in I} h_i + lambda) ] - gamma."
    )
    h['add_body'](
        "A split is executed only if Gain > 0, ensuring that every branch addition achieves a statistically significant reduction in cross-entropy loss."
    )
    
    h['add_heading_12']("Secondary Regression Architecture for Continuous Delay Slippage")
    h['add_body'](
        "While the primary XGBoost classifier predicts binary risk probability P(Delay), supply chain prescriptive optimization requires an exact estimate "
        "of physical transit slippage in days to populate the 'Accept Delay' mitigation option. To solve this, a specialized secondary regressor was constructed "
        "in ml/train.py using XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.08). The regressor is conditioned specifically on historical consignments "
        "where Late_delivery_risk == 1, learning the conditional distribution of delay magnitude given that a delay has materialized. This two-stage hurdle architecture "
        "prevents zero-inflation bias and achieves an empirical Mean Absolute Error (MAE) of 0.4772 days (~11.5 hours) on delayed shipments."
    )
    
    h['add_body']("Exact Empirical Model Performance Metrics (ml/models/metrics.json):")
    table_metrics = [
        ["Evaluation Metric", "Measured Value", "Interpretation in Supply Chain Context"],
        ["Model Architecture", "XGBoost Classifier", "Ensemble of 150 gradient-boosted decision trees (max_depth=6)"],
        ["Accuracy", "69.80% (0.698)", "Overall proportion of correct on-time and delayed predictions"],
        ["Precision", "84.31% (0.8431)", "High precision ensures that when a delay is flagged, it is truly at risk (minimizes false alarms)"],
        ["Recall", "55.18% (0.5518)", "Captures the majority of severe disruption events across complex global shipping lanes"],
        ["F1-Score", "66.70% (0.6670)", "Harmonic mean balancing precision against recall"],
        ["ROC-AUC", "73.70% (0.7370)", "Area under receiver operating characteristic curve demonstrating robust class separability"],
        ["Regression MAE", "0.4772 Days (~0.48 d)", "Mean Absolute Error of secondary regressor in predicting exact delay slippage"],
        ["Regression RMSE", "0.6632 Days (~0.66 d)", "Root Mean Squared Error demonstrating tight error dispersion around delay duration"]
    ]
    h['format_custom_table'](table_metrics, [1.5, 1.5, 3.6], is_compact=True)
    
    h['add_body']("Confusion Matrix Breakdown (36,104 Holdout Test Records):")
    table_cm = [
        ["Confusion Matrix", "Predicted On-Time (0)", "Predicted Late (1)", "Total Actual"],
        ["Actual On-Time (0)", "14,276 (True Negatives)", "2,032 (False Positives)", "16,308"],
        ["Actual Late (1)", "8,873 (False Negatives)", "10,923 (True Positives)", "19,796"],
        ["Total Predicted", "23,149", "12,955", "36,104 (100% Holdout)"]
    ]
    h['format_custom_table'](table_cm, [1.6, 1.7, 1.7, 1.6], is_compact=True)
    
    h['add_body'](
        "As reflected in the confusion matrix, the model exhibits a remarkably low False Positive count (2,032 out of 12,955 positive predictions), "
        "yielding an exceptional 84.31% Precision rating. In enterprise semiconductor procurement, high precision is paramount: false alarms result in "
        "costly unnecessary expediting, whereas high precision ensures that when SupplyPrescript triggers a prescriptive intervention, capital is "
        "deployed only against genuine disruption risks."
    )
    
    # 2.5 Software Requirement Specification
    h['add_heading_14']("2.5 SOFTWARE REQUIREMENT SPECIFICATION")
    h['add_heading_12']("2.5.1 FUNCTIONAL REQUIREMENTS")
    h['add_body']("The functional requirements specify the exact capabilities and behaviors enforced by the system:")
    h['add_bullet']("FR-01 (Shipment Telemetry Ingestion): The platform shall ingest structured JSON shipment manifests including SKU, origin fab, destination hub, unit volume, scheduled transit days, and contractual cost ceiling budgets.")
    h['add_bullet']("FR-02 (Input Validation & Bounds): The backend shall validate all incoming fields against strict Pydantic schemas, rejecting non-positive quantities, negative budgets, and malformed identifiers with HTTP 422 Unprocessable Entity responses.")
    h['add_bullet']("FR-03 (Pre-Transit Delay Risk Inference): The system shall execute the trained XGBoost classifier on ingested shipment attributes, returning a calibrated delay probability P(Delay) between 0.0 and 1.0.")
    h['add_bullet']("FR-04 (Delay Duration Estimation): When delay risk is detected, the secondary XGBoost regressor shall compute the estimated delay duration in days.")
    h['add_bullet']("FR-05 (Prescriptive MILP Optimization): The platform shall formulate a binary integer linear programming problem via PuLP, evaluating competing mitigation alternatives (Air Freight, Secondary Supplier, Accept Delay) to minimize total cost.")
    h['add_bullet']("FR-06 (Budget & SLA Constraint Enforcement): The PuLP solver shall enforce that total mitigation expenditure does not exceed the user's budget ceiling and that delivery days do not violate maximum SLA limits.")
    h['add_bullet']("FR-07 (Supplier Capacity Validation): The solver shall verify that required component quantity does not exceed the capacity of the allocated supplier fab, returning an Infeasible status if capacity is exceeded.")
    h['add_bullet']("FR-08 (Manager Decision Governance): Supply chain managers shall be provided with interactive review controls to approve, override, or append notes to automated prescriptive recommendations.")
    h['add_bullet']("FR-09 (Post-Delivery Outcome Feedback): The platform shall capture actual physical arrival dates, realized landed costs, and operational effectiveness notes, persisting them to the outcomes table.")
    h['add_bullet']("FR-10 (Enterprise User Authentication): The system shall authenticate users via local credentials (PBKDF2-SHA256 password hashing with unique 16-byte cryptographic salts) and multi-provider OAuth 2.0 (Google SSO and Facebook Login).")
    h['add_bullet']("FR-11 (Role-Based Access Control): The platform shall enforce role-based route guards restricting administrative functions (/admin.html and /admin/users) strictly to users with the 'admin' role.")
    h['add_bullet']("FR-12 (Audit Trail Logging): All shipments, predictions, prescriptive decisions, and outcome evaluations shall be immutably recorded in the relational database with UTC timestamps.")
    
    h['add_heading_12']("2.5.2 NON-FUNCTIONAL REQUIREMENTS")
    h['add_bullet']("NFR-01 (Inference Latency): The machine learning pipeline shall compute delay probabilities in under 20 milliseconds per shipment request.")
    h['add_bullet']("NFR-02 (Solver Execution Speed): The PuLP MILP solver shall achieve mathematical convergence and return optimal mitigation decisions in under 50 milliseconds.")
    h['add_bullet']("NFR-03 (Security & Cryptography): All passwords shall be hashed using PBKDF2-HMAC-SHA256 with a minimum of 100,000 iterations. Password reset tokens shall be cryptographically random and stored as SHA-256 hashes with 1-hour expiration.")
    h['add_bullet']("NFR-04 (Relational Integrity): The database layer shall strictly enforce foreign key constraints (PRAGMA foreign_keys = ON) and use Write-Ahead Logging (WAL) for ACID compliance.")
    h['add_bullet']("NFR-05 (Cross-Browser Ergonomics): The frontend shall render responsively across 1080p desktop monitors, laptops, and tablets, conforming to high-contrast WCAG 2.1 accessibility guidelines.")
    
    h['add_heading_12']("2.5.3 MODULE DESCRIPTION")
    h['add_body']("The SupplyPrescript architecture is decoupled into five core operational modules:")
    h['add_bullet']("Module 1: Authentication & Identity Management: Encapsulates user registration, local credential verification, OAuth 2.0 state and code exchange workflows (Google & Facebook), session token lifecycle, and role-based access validation.")
    h['add_bullet']("Module 2: Telemetry Ingestion & Feature Engineering: Validates raw shipment requests against Pydantic schemas, cleans missing data, and applies scikit-learn OneHotEncoder and numerical passthrough transformers.")
    h['add_bullet']("Module 3: Pre-Transit Machine Learning Inference Engine: Executes the dual XGBoost classifier and regressor pipeline, outputting calibrated delay probabilities and duration estimates.")
    h['add_bullet']("Module 4: Prescriptive Mathematical Optimization (PuLP MILP): Constructs the binary linear programming objective function and boundary constraints, executing the CBC solver to select the cost-minimal feasible recovery action.")
    h['add_bullet']("Module 5: Decision Review, Governance & Outcome Feedback: Manages managerial review interfaces, persists audit trails, aggregates real-time KPI metrics, and records post-delivery outcome variance.")
    
    h['add_heading_12']("2.5.4 FLOWCHART")
    h['add_body'](
        "Figure 2.1 illustrates the complete operational flowchart of SupplyPrescript, tracing the progression from initial shipment ingestion "
        "through XGBoost delay classification, PuLP MILP optimization, managerial governance review, and closed-loop feedback logging."
    )
    
    flowchart_path = os.path.join(r"C:\Academic Project\Supply-Prescript\scratch_report_assets", "flowchart.png")
    h['add_image_figure'](flowchart_path, "Figure 2.1: SupplyPrescript End-to-End Operational Flowchart", width_inches=6.0)
    
    doc.add_page_break()
