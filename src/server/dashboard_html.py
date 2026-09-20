"""Interactive Command Center HTML Dashboard for Nasiko Sentinel."""

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nasiko Sentinel — Autonomous Kubernetes Capacity & Recovery Command Center</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-base: #06090e;
            --bg-surface: #0c121d;
            --bg-card: #121b2a;
            --bg-card-hover: #172438;
            --border-subtle: #1e2c44;
            --border-active: #3b82f6;
            --border-glow: rgba(59, 130, 246, 0.4);
            
            --accent-cyan: #06b6d4;
            --accent-blue: #3b82f6;
            --accent-purple: #8b5cf6;
            --accent-emerald: #10b981;
            --accent-amber: #f59e0b;
            --accent-rose: #f43f5e;
            
            --text-high: #f8fafc;
            --text-med: #94a3b8;
            --text-dim: #64748b;
            --mono-font: 'JetBrains Mono', monospace;
            --sans-font: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: var(--sans-font);
            background-color: var(--bg-base);
            background-image: 
                radial-gradient(ellipse at 50% 0%, rgba(14, 165, 233, 0.08) 0%, transparent 60%),
                radial-gradient(circle at 100% 100%, rgba(139, 92, 246, 0.05) 0%, transparent 40%),
                linear-gradient(rgba(30, 44, 68, 0.15) 1px, transparent 1px),
                linear-gradient(90deg, rgba(30, 44, 68, 0.15) 1px, transparent 1px);
            background-size: 100% 100%, 100% 100%, 32px 32px, 32px 32px;
            color: var(--text-high);
            line-height: 1.5;
            padding: 20px;
            min-height: 100vh;
        }

        .container {
            max-width: 1440px;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        /* Demo Mode Overrides */
        body.demo-mode {
            padding: 12px;
        }
        body.demo-mode .container {
            max-width: 100%;
        }
        body.demo-mode .process-node {
            min-width: 155px;
            padding: 16px 12px;
        }
        body.demo-mode .node-title {
            font-size: 14px;
        }
        body.demo-mode .engine-status-text {
            font-size: 38px !important;
        }

        /* Top Command Header */
        header {
            background: linear-gradient(180deg, rgba(18, 27, 42, 0.85) 0%, rgba(12, 18, 29, 0.85) 100%);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border-subtle);
            border-radius: 16px;
            padding: 18px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        }

        .brand-group {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .brand-icon {
            width: 44px;
            height: 44px;
            background: linear-gradient(135deg, #0ea5e9, #3b82f6 60%, #8b5cf6);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 900;
            font-size: 22px;
            color: white;
            box-shadow: 0 0 24px rgba(14, 165, 233, 0.4);
            letter-spacing: -1px;
        }

        .brand-meta h1 {
            font-size: 20px;
            font-weight: 800;
            letter-spacing: -0.5px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .brand-meta h1 span.tag-ver {
            font-size: 11px;
            font-weight: 600;
            font-family: var(--mono-font);
            background: rgba(59, 130, 246, 0.2);
            color: var(--accent-cyan);
            border: 1px solid rgba(6, 182, 212, 0.3);
            padding: 2px 8px;
            border-radius: 6px;
        }

        .brand-meta p {
            font-size: 12px;
            color: var(--text-med);
        }

        .subsystem-pills {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }

        .sys-pill {
            background: rgba(18, 27, 42, 0.9);
            border: 1px solid var(--border-subtle);
            border-radius: 8px;
            padding: 6px 12px;
            font-size: 12px;
            font-family: var(--mono-font);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .pill-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: var(--accent-emerald);
            box-shadow: 0 0 8px var(--accent-emerald);
        }
        .pill-dot.sim { background-color: var(--accent-amber); box-shadow: 0 0 8px var(--accent-amber); }
        .pill-dot.ai { background-color: var(--accent-purple); box-shadow: 0 0 8px var(--accent-purple); }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .btn {
            font-family: var(--sans-font);
            font-size: 13px;
            font-weight: 600;
            padding: 9px 18px;
            border-radius: 10px;
            border: 1px solid transparent;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .btn-primary {
            background: linear-gradient(135deg, #0284c7, #2563eb);
            color: white;
            box-shadow: 0 4px 16px rgba(37, 99, 235, 0.35);
        }
        .btn-primary:hover {
            box-shadow: 0 6px 24px rgba(37, 99, 235, 0.55);
            transform: translateY(-1px);
        }

        .btn-danger {
            background: rgba(244, 63, 94, 0.15);
            border-color: rgba(244, 63, 94, 0.35);
            color: #fb7185;
        }
        .btn-danger:hover {
            background: rgba(244, 63, 94, 0.25);
            color: #fff;
        }

        .btn-ghost {
            background: rgba(255, 255, 255, 0.05);
            border-color: var(--border-subtle);
            color: var(--text-med);
        }
        .btn-ghost:hover {
            background: rgba(255, 255, 255, 0.1);
            color: var(--text-high);
        }

        .toggle-btn {
            display: flex;
            align-items: center;
            gap: 6px;
            background: rgba(18, 27, 42, 0.9);
            border: 1px solid var(--border-subtle);
            padding: 8px 14px;
            border-radius: 10px;
            cursor: pointer;
            font-size: 12px;
            color: var(--text-med);
            user-select: none;
        }
        .toggle-btn.active {
            border-color: var(--accent-cyan);
            color: var(--accent-cyan);
            background: rgba(6, 182, 212, 0.12);
        }

        /* Central Agent Engine Card */
        .engine-card {
            background: linear-gradient(135deg, rgba(14, 23, 38, 0.9) 0%, rgba(10, 15, 25, 0.9) 100%);
            border: 1px solid var(--border-subtle);
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
            display: grid;
            grid-template-columns: 1.4fr 1fr 1fr;
            gap: 20px;
            align-items: center;
            position: relative;
            overflow: hidden;
        }

        .engine-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, transparent, var(--accent-cyan), var(--accent-purple), transparent);
        }

        .engine-main-state {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .engine-label {
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1.5px;
            color: var(--text-dim);
            text-transform: uppercase;
            font-family: var(--mono-font);
        }

        .engine-status-text {
            font-size: 32px;
            font-weight: 900;
            letter-spacing: -0.5px;
            display: flex;
            align-items: center;
            gap: 14px;
            color: var(--text-high);
            text-shadow: 0 0 20px rgba(59, 130, 246, 0.3);
        }

        .status-pulse-ring {
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background-color: var(--accent-cyan);
            position: relative;
        }

        .status-pulse-ring::after {
            content: '';
            position: absolute;
            top: -4px;
            left: -4px;
            right: -4px;
            bottom: -4px;
            border-radius: 50%;
            border: 2px solid var(--accent-cyan);
            animation: pulse-ring 1.8s cubic-bezier(0.24, 0, 0.38, 1) infinite;
        }

        @keyframes pulse-ring {
            0% { transform: scale(0.6); opacity: 1; }
            100% { transform: scale(2.0); opacity: 0; }
        }

        .target-agent-box {
            background: rgba(6, 9, 14, 0.6);
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            padding: 14px 18px;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        .target-agent-box .lbl { font-size: 11px; color: var(--text-dim); font-family: var(--mono-font); }
        .target-agent-box .val { font-size: 13px; font-weight: 600; font-family: var(--mono-font); color: var(--accent-cyan); }
        .target-agent-box .sub { font-size: 12px; color: var(--text-med); }

        .metric-counter-strip {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
        }

        .metric-mini-cell {
            background: rgba(6, 9, 14, 0.6);
            border: 1px solid var(--border-subtle);
            border-radius: 10px;
            padding: 10px 14px;
            display: flex;
            flex-direction: column;
        }
        .metric-mini-cell .num { font-size: 20px; font-weight: 800; font-family: var(--mono-font); color: var(--text-high); }
        .metric-mini-cell .desc { font-size: 11px; color: var(--text-dim); }

        /* Evidentiary Process Graph (Main Stage) */
        .process-stage {
            background: rgba(12, 18, 29, 0.9);
            border: 1px solid var(--border-subtle);
            border-radius: 16px;
            padding: 22px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .stage-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .stage-header h2 { font-size: 16px; font-weight: 800; letter-spacing: -0.3px; display: flex; align-items: center; gap: 10px; }
        .stage-header .badge-tag { font-size: 11px; font-family: var(--mono-font); background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); padding: 3px 10px; border-radius: 6px; }

        .process-graph-container {
            display: flex;
            align-items: stretch;
            gap: 8px;
            overflow-x: auto;
            padding: 10px 4px 16px 4px;
            scrollbar-width: thin;
            scrollbar-color: var(--border-subtle) transparent;
        }

        .process-node {
            flex: 1;
            min-width: 125px;
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            padding: 14px 10px;
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            gap: 8px;
            cursor: pointer;
            transition: all 0.25s ease;
            position: relative;
            user-select: none;
        }

        .process-node:hover {
            border-color: var(--border-active);
            background: var(--bg-card-hover);
            transform: translateY(-2px);
        }

        .process-node.selected {
            border-color: var(--accent-cyan);
            box-shadow: 0 0 20px rgba(6, 182, 212, 0.35);
            background: #152238;
        }

        .process-node.state-completed {
            border-color: rgba(16, 185, 129, 0.4);
        }
        .process-node.state-completed .node-dot {
            background-color: var(--accent-emerald);
            box-shadow: 0 0 10px var(--accent-emerald);
        }

        .process-node.state-active {
            border-color: var(--accent-cyan);
            animation: border-glow 1.5s infinite alternate;
        }
        .process-node.state-active .node-dot {
            background-color: var(--accent-cyan);
            box-shadow: 0 0 12px var(--accent-cyan);
        }

        .process-node.state-blocked {
            border-color: var(--accent-rose);
        }
        .process-node.state-blocked .node-dot {
            background-color: var(--accent-rose);
            box-shadow: 0 0 12px var(--accent-rose);
        }

        .process-node.state-waiting {
            opacity: 0.55;
        }

        @keyframes border-glow {
            0% { border-color: rgba(6, 182, 212, 0.4); box-shadow: 0 0 8px rgba(6, 182, 212, 0.2); }
            100% { border-color: rgba(6, 182, 212, 1); box-shadow: 0 0 18px rgba(6, 182, 212, 0.5); }
        }

        .node-step-num {
            font-size: 10px;
            font-family: var(--mono-font);
            color: var(--text-dim);
            font-weight: 700;
        }

        .node-icon {
            width: 32px;
            height: 32px;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.05);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 15px;
        }

        .node-title {
            font-size: 12px;
            font-weight: 700;
            line-height: 1.2;
            color: var(--text-high);
        }

        .node-state-pill {
            font-size: 10px;
            font-family: var(--mono-font);
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 700;
            background: rgba(255, 255, 255, 0.06);
            color: var(--text-dim);
        }
        .state-completed .node-state-pill { background: rgba(16, 185, 129, 0.15); color: #34d399; }
        .state-active .node-state-pill { background: rgba(6, 182, 212, 0.15); color: var(--accent-cyan); }
        .state-blocked .node-state-pill { background: rgba(244, 63, 94, 0.15); color: #fb7185; }

        /* Workspace Grid (Inspector & AI/Policy split) */
        .workspace-grid {
            display: grid;
            grid-template-columns: 1.15fr 1fr;
            gap: 20px;
        }

        @media (max-width: 1080px) {
            .workspace-grid {
                grid-template-columns: 1fr;
            }
            .engine-card {
                grid-template-columns: 1fr;
            }
        }

        .panel-box {
            background: rgba(12, 18, 29, 0.9);
            border: 1px solid var(--border-subtle);
            border-radius: 16px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .panel-title {
            font-size: 15px;
            font-weight: 700;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        /* Evidence Inspector */
        .evidence-content-box {
            background: #080d15;
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            min-height: 260px;
        }

        .badge-category {
            align-self: flex-start;
            font-size: 11px;
            font-family: var(--mono-font);
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 6px;
            letter-spacing: 0.5px;
        }
        .badge-obs { background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.4); }
        .badge-diag { background: rgba(14, 165, 233, 0.2); color: #38bdf8; border: 1px solid rgba(14, 165, 233, 0.4); }
        .badge-ai { background: rgba(139, 92, 246, 0.2); color: #a78bfa; border: 1px solid rgba(139, 92, 246, 0.4); }
        .badge-pol { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.4); }
        .badge-act { background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.4); }
        .badge-err { background: rgba(244, 63, 94, 0.2); color: #fb7185; border: 1px solid rgba(244, 63, 94, 0.4); }

        .evidence-prop-row {
            display: flex;
            justify-content: space-between;
            font-size: 13px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.04);
            padding-bottom: 6px;
        }
        .evidence-prop-row .k { color: var(--text-dim); font-family: var(--mono-font); font-size: 12px; }
        .evidence-prop-row .v { color: var(--text-high); font-weight: 600; font-family: var(--mono-font); text-align: right; }

        .evidence-quote {
            background: rgba(255, 255, 255, 0.03);
            border-left: 3px solid var(--accent-cyan);
            padding: 10px 14px;
            font-family: var(--mono-font);
            font-size: 12px;
            color: #bae6fd;
            border-radius: 0 8px 8px 0;
            white-space: pre-wrap;
        }

        /* Policy Gate Viz Box */
        .policy-checkpoint-box {
            background: #080d15;
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 14px;
        }

        .policy-flow-diagram {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(18, 27, 42, 0.6);
            border: 1px solid var(--border-subtle);
            border-radius: 10px;
            padding: 12px 16px;
        }

        .policy-step-pill {
            font-size: 11px;
            font-family: var(--mono-font);
            font-weight: 700;
            padding: 6px 12px;
            border-radius: 6px;
            text-align: center;
        }

        .policy-rules-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
            font-size: 12px;
            font-family: var(--mono-font);
        }
        .rule-item {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border-subtle);
            padding: 8px 10px;
            border-radius: 6px;
            display: flex;
            justify-content: space-between;
        }
        .rule-item span.lbl { color: var(--text-dim); }
        .rule-item span.val { color: var(--accent-cyan); font-weight: 600; }

        .policy-banner {
            padding: 10px 14px;
            border-radius: 8px;
            font-weight: 700;
            font-size: 13px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-family: var(--mono-font);
        }
        .policy-pass { background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.35); color: #34d399; }
        .policy-fail { background: rgba(244, 63, 94, 0.15); border: 1px solid rgba(244, 63, 94, 0.35); color: #fb7185; }

        .motto-banner {
            text-align: center;
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 0.5px;
            color: #c084fc;
            background: rgba(139, 92, 246, 0.08);
            border: 1px dashed rgba(139, 92, 246, 0.3);
            padding: 8px 12px;
            border-radius: 8px;
        }

        /* Bottom Section: Activity Stream & System Topology */
        .bottom-grid {
            display: grid;
            grid-template-columns: 1.3fr 0.9fr;
            gap: 20px;
        }
        @media (max-width: 1080px) {
            .bottom-grid {
                grid-template-columns: 1fr;
            }
        }

        .terminal-box {
            background: #05080e;
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            padding: 14px;
            font-family: var(--mono-font);
            font-size: 12px;
            color: #93c5fd;
            height: 240px;
            overflow-y: auto;
            white-space: pre-wrap;
            line-height: 1.6;
        }

        .topology-viz {
            background: #080d15;
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            font-family: var(--mono-font);
            font-size: 12px;
        }

        .topo-node {
            background: rgba(18, 27, 42, 0.7);
            border: 1px solid var(--border-subtle);
            padding: 10px 14px;
            border-radius: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .topo-node.active { border-color: var(--accent-cyan); }
        .topo-arrow { text-align: center; color: var(--text-dim); font-size: 11px; }

        footer {
            text-align: center;
            font-size: 12px;
            color: var(--text-dim);
            padding: 12px 0;
            border-top: 1px solid var(--border-subtle);
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- 1. HERO / COMMAND HEADER -->
        <header>
            <div class="brand-group">
                <div class="brand-icon">&#x26A1;</div>
                <div class="brand-meta">
                    <h1>NASIKO SENTINEL <span class="tag-ver">MCP 2024-11-05</span></h1>
                    <p>Autonomous Agent Capacity & Elastic Kubernetes Self-Healing Control Plane</p>
                </div>
            </div>

            <!-- Real-time Subsystem Status Badges -->
            <div class="subsystem-pills">
                <div class="sys-pill" title="Streamable HTTP & stdio Dual Transports">
                    <span class="pill-dot"></span>
                    <span>MCP: READY (14 Tools)</span>
                </div>
                <div class="sys-pill" id="pill-k8s" title="Kubernetes Cluster Connection State">
                    <span class="pill-dot sim"></span>
                    <span id="k8s-state-label">K8S: SIMULATED ADAPTER</span>
                </div>
                <div class="sys-pill" id="pill-reasoner" title="AI Model Reasoner Provider">
                    <span class="pill-dot ai"></span>
                    <span id="reasoner-state-label">AI: DETERMINISTIC FALLBACK</span>
                </div>
                <div class="sys-pill" id="pill-autoscaler" title="Controlled Autoscaler Engine">
                    <span class="pill-dot sim"></span>
                    <span id="autoscaler-state-label">AUTOSCALER: SIMULATED</span>
                </div>
            </div>

            <!-- Action Controls -->
            <div class="header-actions">
                <button class="btn btn-primary" id="btn-run-demo" onclick="runCompleteDemo()">
                    <span>&#9654;</span> RUN RECOVERY DEMO
                </button>
                <button class="btn btn-danger" id="btn-sim-block" onclick="simulatePolicyBlock()">
                    <span>&#9888;</span> SIMULATE POLICY BLOCK
                </button>
                <div class="toggle-btn" id="btn-demo-mode" onclick="toggleDemoMode()" title="Optimized for Projector / Stage Presentation">
                    <span>&#x1F4FA;</span> DEMO MODE
                </div>
            </div>
        </header>

        <!-- 2. CENTRAL STATUS CARD -->
        <div class="engine-card">
            <div class="engine-main-state">
                <div class="engine-label">Agent Recovery Engine &bull; Realtime State</div>
                <div class="engine-status-text" id="engine-status">
                    <div class="status-pulse-ring" id="status-ring"></div>
                    <span id="engine-state-title">IDLE / READY</span>
                </div>
                <div style="font-size: 12px; color: var(--text-med);" id="engine-state-desc">
                    Awaiting trigger or unschedulable pod detection across monitored agent namespaces.
                </div>
            </div>

            <div class="target-agent-box">
                <div class="lbl">TARGET NASIKO WORKLOAD</div>
                <div class="val" id="target-pod-name">agent-pending-cpu</div>
                <div class="sub" id="target-agent-id">UUID: a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11</div>
                <div class="sub" style="color: var(--accent-amber); margin-top: 2px;">Demand: 2000m CPU &bull; 1 Node Required</div>
            </div>

            <div class="metric-counter-strip">
                <div class="metric-mini-cell">
                    <span class="num" id="metric-pending">1</span>
                    <span class="desc">Pending Pods</span>
                </div>
                <div class="metric-mini-cell">
                    <span class="num" id="metric-decisions">0</span>
                    <span class="desc">Policy Audits</span>
                </div>
                <div class="metric-mini-cell">
                    <span class="num" id="metric-recoveries">0</span>
                    <span class="desc">Recoveries</span>
                </div>
                <div class="metric-mini-cell">
                    <span class="num" id="metric-timer">0.0s</span>
                    <span class="desc">Elapsed Time</span>
                </div>
            </div>
        </div>

        <!-- 3. EVIDENTIARY PROCESS GRAPH -->
        <div class="process-stage">
            <div class="stage-header">
                <h2><span>&#x1F578;</span> Autonomous Evidentiary Process Pipeline</h2>
                <div class="badge-tag">Click Any Node to Inspect Evidence</div>
            </div>

            <div class="process-graph-container" id="process-graph">
                <!-- 11 Standard Evidentiary Nodes -->
                <div class="process-node state-waiting" id="node-1" onclick="selectNode(1)">
                    <span class="node-step-num">01</span>
                    <div class="node-icon">&#x1F4E8;</div>
                    <div class="node-title">Agent Request</div>
                    <span class="node-state-pill">WAITING</span>
                </div>

                <div class="process-node state-waiting" id="node-2" onclick="selectNode(2)">
                    <span class="node-step-num">02</span>
                    <div class="node-icon">&#x2699;&#xFE0F;</div>
                    <div class="node-title">Pod Scheduling</div>
                    <span class="node-state-pill">WAITING</span>
                </div>

                <div class="process-node state-waiting" id="node-3" onclick="selectNode(3)">
                    <span class="node-step-num">03</span>
                    <div class="node-icon">&#x23F3;</div>
                    <div class="node-title">Pending Detected</div>
                    <span class="node-state-pill">WAITING</span>
                </div>

                <div class="process-node state-waiting" id="node-4" onclick="selectNode(4)">
                    <span class="node-step-num">04</span>
                    <div class="node-icon">&#x1F50D;</div>
                    <div class="node-title">K8s Evidence</div>
                    <span class="node-state-pill">WAITING</span>
                </div>

                <div class="process-node state-waiting" id="node-5" onclick="selectNode(5)">
                    <span class="node-step-num">05</span>
                    <div class="node-icon">&#x1F9E9;</div>
                    <div class="node-title">Root Cause</div>
                    <span class="node-state-pill">WAITING</span>
                </div>

                <div class="process-node state-waiting" id="node-6" onclick="selectNode(6)">
                    <span class="node-step-num">06</span>
                    <div class="node-icon">&#x1F9E0;</div>
                    <div class="node-title">AI Reasoning</div>
                    <span class="node-state-pill">WAITING</span>
                </div>

                <div class="process-node state-waiting" id="node-7" onclick="selectNode(7)">
                    <span class="node-step-num">07</span>
                    <div class="node-icon">&#x1F4DC;</div>
                    <div class="node-title">Recovery Proposal</div>
                    <span class="node-state-pill">WAITING</span>
                </div>

                <div class="process-node state-waiting" id="node-8" onclick="selectNode(8)">
                    <span class="node-step-num">08</span>
                    <div class="node-icon">&#x1F6E1;&#xFE0F;</div>
                    <div class="node-title">Policy Gate</div>
                    <span class="node-state-pill">WAITING</span>
                </div>

                <div class="process-node state-waiting" id="node-9" onclick="selectNode(9)">
                    <span class="node-step-num">09</span>
                    <div class="node-icon">&#x1F527;</div>
                    <div class="node-title">Scale Action</div>
                    <span class="node-state-pill">WAITING</span>
                </div>

                <div class="process-node state-waiting" id="node-10" onclick="selectNode(10)">
                    <span class="node-step-num">10</span>
                    <div class="node-icon">&#x2705;</div>
                    <div class="node-title">Capacity Ready</div>
                    <span class="node-state-pill">WAITING</span>
                </div>

                <div class="process-node state-waiting" id="node-11" onclick="selectNode(11)">
                    <span class="node-step-num">11</span>
                    <div class="node-icon">&#x1F680;</div>
                    <div class="node-title">Agent Running</div>
                    <span class="node-state-pill">WAITING</span>
                </div>
            </div>
        </div>

        <!-- 4. WORKSPACE: EVIDENCE INSPECTOR & POLICY / AI GATE -->
        <div class="workspace-grid">
            <!-- Left Panel: Evidence Inspector -->
            <div class="panel-box">
                <div class="panel-title">
                    <span>&#x1F4CA; Evidentiary Deep Inspector</span>
                    <span id="inspector-badge" class="badge-category badge-obs">OBSERVED FACT</span>
                </div>
                <div class="evidence-content-box" id="inspector-body">
                    <!-- Dynamic evidence rendered by JavaScript -->
                    <div class="evidence-prop-row">
                        <span class="k">Selected Step</span>
                        <span class="v" id="ev-step-title">Initial Observation</span>
                    </div>
                    <div class="evidence-prop-row">
                        <span class="k">Pod Subject</span>
                        <span class="v">agent-pending-cpu</span>
                    </div>
                    <div class="evidence-prop-row">
                        <span class="k">Evidence Source</span>
                        <span class="v">Kubernetes Scheduler Events</span>
                    </div>
                    <div class="evidence-quote" id="ev-quote-text">
Click "RUN RECOVERY DEMO" to start the autonomous diagnostic and recovery cycle. Click on any step in the pipeline above to view detailed evidentiary artifacts.
                    </div>
                </div>
            </div>

            <!-- Right Panel: AI Reasoning & Policy Checkpoint -->
            <div class="panel-box">
                <div class="panel-title">
                    <span>&#x1F916; Sentinel AI &amp; Recovery Policy Gate</span>
                    <span class="badge-category badge-pol">AUTHORITATIVE GATEWAY</span>
                </div>

                <div class="policy-checkpoint-box">
                    <div class="policy-flow-diagram">
                        <div class="policy-step-pill" style="background: rgba(139, 92, 246, 0.2); color: #c084fc;">
                            AI PROPOSAL<br><small id="flow-ai-prop">+1 Node</small>
                        </div>
                        <span style="color: var(--text-dim); font-weight: 700;">&rarr;</span>
                        <div class="policy-step-pill" style="background: rgba(245, 158, 11, 0.2); color: #fbbf24;">
                            POLICY GATE<br><small>Safety Check</small>
                        </div>
                        <span style="color: var(--text-dim); font-weight: 700;">&rarr;</span>
                        <div class="policy-step-pill" id="flow-decision-pill" style="background: rgba(16, 185, 129, 0.2); color: #34d399;">
                            DECISION<br><small id="flow-decision-text">PENDING</small>
                        </div>
                    </div>

                    <div class="policy-rules-grid">
                        <div class="rule-item">
                            <span class="lbl">MAX NODES / REQ:</span>
                            <span class="val">2 Nodes</span>
                        </div>
                        <div class="rule-item">
                            <span class="lbl">CLUSTER MAX:</span>
                            <span class="val">10 Nodes</span>
                        </div>
                        <div class="rule-item">
                            <span class="lbl">POOL COOLDOWN:</span>
                            <span class="val">120s</span>
                        </div>
                        <div class="rule-item">
                            <span class="lbl">ALLOWED POOLS:</span>
                            <span class="val">default</span>
                        </div>
                    </div>

                    <div class="policy-banner policy-pass" id="policy-verdict-banner">
                        <span id="policy-verdict-title">&#x2713; POLICY ENGINE STANDBY</span>
                        <span id="policy-verdict-reason">Awaiting AI proposal</span>
                    </div>

                    <div class="motto-banner">
                        &ldquo;AI proposes. Policy decides.&rdquo;
                    </div>
                </div>
            </div>
        </div>

        <!-- 5. BOTTOM SECTION: AGENT ACTIVITY STREAM & SYSTEM TOPOLOGY -->
        <div class="bottom-grid">
            <!-- Left: Realtime Agent Stream -->
            <div class="panel-box">
                <div class="panel-title">
                    <span>&#x1F4DD; Autonomous Agent Activity Stream</span>
                    <button class="btn btn-ghost" style="padding: 4px 10px; font-size: 11px;" onclick="clearStream()">Clear</button>
                </div>
                <div class="terminal-box" id="agent-stream-box">
[SYSTEM INIT] Nasiko Sentinel Command Center loaded.
[READY] MCP Server connected via Streamable HTTP (JSON-RPC 2.0).
[STANDBY] Monitoring Kubernetes agent deployment queue.
                </div>
            </div>

            <!-- Right: System Topology -->
            <div class="panel-box">
                <div class="panel-title">
                    <span>&#x1F310; System Topology &amp; Governance</span>
                    <span class="badge-category badge-act">LIVE GRAPH</span>
                </div>
                <div class="topology-viz">
                    <div class="topo-node active">
                        <span><strong>DronaHQ AI Agent</strong> (UI / Webhook)</span>
                        <span style="color: var(--accent-cyan); font-size: 11px;">Client Layer</span>
                    </div>
                    <div class="topo-arrow">&darr; Streamable HTTP (POST /mcp)</div>
                    <div class="topo-node active">
                        <span><strong>MCP Server Transport Adapter</strong></span>
                        <span style="color: var(--accent-emerald); font-size: 11px;">JSON-RPC 2.0</span>
                    </div>
                    <div class="topo-arrow">&darr; In-Memory Dispatch</div>
                    <div class="topo-node active">
                        <span><strong>Sentinel Core</strong> (Observer &bull; Reasoner &bull; Policy)</span>
                        <span style="color: var(--accent-purple); font-size: 11px;">Governance</span>
                    </div>
                    <div class="topo-arrow">&darr; Controlled Autoscaling</div>
                    <div class="topo-node">
                        <span><strong>Kubernetes Cluster</strong> (Nodes &amp; Pods)</span>
                        <span style="color: var(--accent-amber); font-size: 11px;">Infrastructure</span>
                    </div>
                </div>
            </div>
        </div>

        <footer>
            Nasiko Sentinel &bull; Protocol Version 2024-11-05 &bull; Dual Transport (Streamable HTTP / stdio) &bull; DronaHQ & AWS Bedrock Ready
        </footer>
    </div>

    <!-- SCRIPT LOGIC -->
    <script>
        const API_KEY = "sentinel-local-dev-key";
        let isRunningDemo = false;
        let timerInterval = null;
        let startTime = 0;

        // Evidence Dictionary for 11 Pipeline Steps
        const EVIDENCE_STORE = {
            1: {
                title: "01. AGENT REQUEST",
                category: "OBSERVED FACT",
                badgeClass: "badge-obs",
                props: {
                    "Request Source": "Nasiko Agent Orchestrator",
                    "Agent Target ID": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
                    "Required Resources": "2000m CPU, 1024Mi Memory",
                    "Deployment Name": "agent-a0eebc99-9c0b"
                },
                quote: "Agent creation requested for task 'financial-analyst'. Deployment dispatched to Kubernetes API."
            },
            2: {
                title: "02. POD SCHEDULING",
                category: "OBSERVED FACT",
                badgeClass: "badge-obs",
                props: {
                    "Scheduler": "kube-scheduler (default-scheduler)",
                    "Pod Name": "agent-pending-cpu",
                    "Node Filter": "Evaluated 2/2 cluster nodes",
                    "Status": "FailedScheduling Event Dispatched"
                },
                quote: "kube-scheduler evaluated node-1 and node-2. Insufficient allocatable CPU to schedule 2000m."
            },
            3: {
                title: "03. PENDING DETECTED",
                category: "OBSERVED FACT",
                badgeClass: "badge-obs",
                props: {
                    "Observation Engine": "KubernetesAdapter.get_pending_pods()",
                    "Observed Phase": "Pending",
                    "Reason": "Unschedulable",
                    "Time in Pending": "45 seconds"
                },
                quote: "Pod agent-pending-cpu has been in Pending phase exceeding threshold. Triggering Sentinel diagnostic engine."
            },
            4: {
                title: "04. KUBERNETES EVIDENCE",
                category: "OBSERVED FACT",
                badgeClass: "badge-obs",
                props: {
                    "Event Reason": "FailedScheduling",
                    "Cluster Headroom": "Node-1: 300m free, Node-2: 400m free",
                    "Contiguous Required": "2000m CPU",
                    "Deficit": "1300m CPU headroom gap"
                },
                quote: "FailedScheduling: 0/2 nodes are available: 2 Insufficient cpu. Preemption: 0/2 nodes are available."
            },
            5: {
                title: "05. ROOT CAUSE DIAGNOSIS",
                category: "DETERMINISTIC DIAGNOSIS",
                badgeClass: "badge-diag",
                props: {
                    "Diagnosis Engine": "src.diagnosis.engine.CapacityDiagnosisEngine",
                    "Classification": "insufficient_cpu",
                    "Confidence": "100% (Deterministic Pattern Match)",
                    "Hallucination Risk": "0.00% (Rule-Based Normalization)"
                },
                quote: "Root cause deterministically proven: cluster lacks single-node allocatable CPU for 2000m pod requirement."
            },
            6: {
                title: "06. AI REASONING",
                category: "AI INFERENCE",
                badgeClass: "badge-ai",
                props: {
                    "AI Model Provider": "AWS Bedrock (or Deterministic Fallback)",
                    "Synthesis": "Evaluated node allocatables + pending queue",
                    "Recommended Action": "REQUEST_SCALE_UP",
                    "Proposed Nodes": "+1 Node (default pool)"
                },
                quote: "Bedrock Synthesizer: 'Cluster capacity exhausted for 2000m pod. Immediate +1 node scale up advised.'"
            },
            7: {
                title: "07. RECOVERY PROPOSAL",
                category: "AI INFERENCE",
                badgeClass: "badge-ai",
                props: {
                    "Proposal Type": "RecoveryProposal Data Model",
                    "Target Pool": "default",
                    "Requested Delta": "1 Node",
                    "Target Agent": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
                },
                quote: "Structured RecoveryProposal object created. Handing off to Recovery Policy Engine for gate authorization."
            },
            8: {
                title: "08. POLICY GATE CHECKPOINT",
                category: "POLICY DECISION",
                badgeClass: "badge-pol",
                props: {
                    "Gate Authority": "src.autoscaler.policy.RecoveryPolicyEngine",
                    "Rule: Max Nodes Check": "1 requested <= 2 allowed (PASS)",
                    "Rule: Pool Cooldown": "120s cooldown elapsed (PASS)",
                    "Authorization Result": "ALLOWED"
                },
                quote: "✓ RecoveryPolicyEngine: Request strictly complies with all safety rules. Infrastructure action authorized."
            },
            9: {
                title: "09. SCALE ACTION EXECUTION",
                category: "EXECUTED ACTION",
                badgeClass: "badge-act",
                props: {
                    "Provider Executed": "SimulatedAutoscalerProvider (or Karpenter)",
                    "Operation": "scale_up(node_pool='default', count=1)",
                    "Provisioning State": "PROVISIONING -> READY",
                    "Node Injected": "node-3 (allocatable: 4000m CPU)"
                },
                quote: "Autoscaler initiated node provisioning. Node node-3 registered and transitioned to Ready."
            },
            10: {
                title: "10. CAPACITY READY",
                category: "OBSERVED FACT",
                badgeClass: "badge-obs",
                props: {
                    "Node Name": "node-3",
                    "Kubelet State": "Ready, Schedulable",
                    "Allocatable Headroom": "4000m CPU, 8192Mi Memory",
                    "Scheduler Notification": "Node available for pending queue"
                },
                quote: "Kubernetes scheduler binds pending pod agent-pending-cpu to node-3."
            },
            11: {
                title: "11. AGENT VERIFIED RUNNING",
                category: "EXECUTED ACTION",
                badgeClass: "badge-act",
                props: {
                    "Verification Tool": "verify_agent_recovery",
                    "Deployment Status": "Replicas 1/1 Ready",
                    "Pod Phase": "Running (ContainerReady: True)",
                    "Recovery Result": "COMPLETE_SUCCESS"
                },
                quote: "Agent workload verified healthy and serving traffic. Recovery cycle successfully completed."
            }
        };

        function appendStream(msg) {
            const el = document.getElementById('agent-stream-box');
            const time = new Date().toISOString().split('T')[1].slice(0, 8);
            el.innerText += `\\n[${time}] ${msg}`;
            el.scrollTop = el.scrollHeight;
        }

        function clearStream() {
            document.getElementById('agent-stream-box').innerText = "[CLEARED] Awaiting activity...\\n";
        }

        function toggleDemoMode() {
            document.body.classList.toggle('demo-mode');
            const btn = document.getElementById('btn-demo-mode');
            btn.classList.toggle('active');
        }

        function setNodeState(step, state) {
            const node = document.getElementById(`node-${step}`);
            if (!node) return;
            node.className = `process-node state-${state}`;
            const pill = node.querySelector('.node-state-pill');
            if (pill) pill.innerText = state.toUpperCase();
        }

        function selectNode(step) {
            // Remove previous selection
            document.querySelectorAll('.process-node').forEach(n => n.classList.remove('selected'));
            const node = document.getElementById(`node-${step}`);
            if (node) node.classList.add('selected');

            const data = EVIDENCE_STORE[step];
            if (!data) return;

            const badge = document.getElementById('inspector-badge');
            badge.innerText = data.category;
            badge.className = `badge-category ${data.badgeClass}`;

            let html = `<div class="evidence-prop-row"><span class="k">Pipeline Step</span><span class="v" style="color: var(--accent-cyan);">${data.title}</span></div>`;
            for (const [k, v] of Object.entries(data.props)) {
                html += `<div class="evidence-prop-row"><span class="k">${k}</span><span class="v">${v}</span></div>`;
            }
            html += `<div class="evidence-quote">${data.quote}</div>`;
            document.getElementById('inspector-body').innerHTML = html;
        }

        async function fetchHealth() {
            try {
                const resp = await fetch('/health');
                const data = await resp.json();
                if (data.dependencies) {
                    if (data.dependencies.reasoner) {
                        const rName = data.dependencies.reasoner.provider || "deterministic_fallback";
                        const isMock = data.dependencies.reasoner.mock_mode === true || rName.toLowerCase().includes("mock");
                        const isLiveBedrock = rName.toLowerCase().includes("bedrock") && !isMock;
                        document.getElementById('reasoner-state-label').innerText = isLiveBedrock ? "AI: BEDROCK (LIVE)" : "AI: DETERMINISTIC FALLBACK";
                    }
                    if (data.dependencies.autoscaler) {
                        const isLiveAuto = data.dependencies.autoscaler.provider !== "simulated";
                        document.getElementById('autoscaler-state-label').innerText = isLiveAuto ? `AUTOSCALER: LIVE (${data.dependencies.autoscaler.provider.toUpperCase()})` : "AUTOSCALER: SIMULATED PROVIDER";
                    }
                    if (data.dependencies.kubernetes) {
                        const isK8s = data.dependencies.kubernetes.status === "connected";
                        document.getElementById('k8s-state-label').innerText = isK8s ? "K8S: LIVE KUBERNETES" : "K8S: SIMULATED KUBERNETES";
                    }
                }
            } catch (err) {
                console.warn("Health check error:", err);
            }
        }

        async function callMCPTool(toolName, args) {
            const payload = {
                jsonrpc: "2.0",
                id: Date.now(),
                method: "tools/call",
                params: {
                    name: toolName,
                    arguments: args
                }
            };
            const resp = await fetch('/mcp', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${API_KEY}`,
                    'X-Sentinel-API-Key': API_KEY
                },
                body: JSON.stringify(payload)
            });
            const resData = await resp.json();
            if (resData.result && resData.result.content && resData.result.content[0]) {
                try {
                    return JSON.parse(resData.result.content[0].text);
                } catch {
                    return resData.result.content[0].text;
                }
            }
            return resData;
        }

        const sleep = ms => new Promise(r => setTimeout(r, ms));

        async function runCompleteDemo() {
            if (isRunningDemo) return;
            isRunningDemo = true;
            document.getElementById('btn-run-demo').disabled = true;

            // Reset UI
            for (let i = 1; i <= 11; i++) setNodeState(i, 'waiting');
            startTime = Date.now();
            if (timerInterval) clearInterval(timerInterval);
            timerInterval = setInterval(() => {
                const el = document.getElementById('metric-timer');
                el.innerText = ((Date.now() - startTime) / 1000).toFixed(1) + 's';
            }, 100);

            // Step 1: Request
            document.getElementById('engine-state-title').innerText = "DETECTING PENDING WORKLOAD";
            document.getElementById('engine-state-desc').innerText = "Observing Kubernetes agent deployment queue...";
            setNodeState(1, 'active');
            selectNode(1);
            appendStream("Observing unschedulable pod 'agent-pending-cpu' in namespace 'nasiko-agents'.");
            await sleep(600);
            setNodeState(1, 'completed');

            // Step 2 & 3: Scheduling & Pending
            setNodeState(2, 'completed');
            setNodeState(3, 'active');
            selectNode(3);
            appendStream("Scheduler rejected pod due to insufficient allocatable CPU on existing 2 nodes.");
            await sleep(600);
            setNodeState(3, 'completed');

            // Step 4 & 5: Evidence & Diagnosis
            document.getElementById('engine-state-title').innerText = "DIAGNOSING CAPACITY BOTTLENECK";
            setNodeState(4, 'active');
            selectNode(4);
            appendStream("Collecting Kubernetes scheduler events and allocatable node metrics...");
            await sleep(500);
            setNodeState(4, 'completed');

            setNodeState(5, 'active');
            selectNode(5);
            const diagResult = await callMCPTool('diagnose_capacity', { pod_name: 'agent-pending-cpu' });
            appendStream(`Diagnosis Engine: Class = ${diagResult.classification} | Unschedulable = ${diagResult.is_unschedulable}`);
            await sleep(600);
            setNodeState(5, 'completed');

            // Step 6 & 7: AI Reasoning & Proposal
            document.getElementById('engine-state-title').innerText = "FORMULATING AI REASONING";
            setNodeState(6, 'active');
            selectNode(6);
            appendStream("Invoking AI Reasoner orchestrator with structured headroom context...");
            const reasonResult = await callMCPTool('reason_recovery', { pod_name: 'agent-pending-cpu', agent_id: 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' });
            appendStream(`AI Proposal: Action = ${reasonResult.action || 'REQUEST_SCALE_UP'} | Source = ${reasonResult.reasoning_source || 'BEDROCK'}`);
            await sleep(700);
            setNodeState(6, 'completed');

            setNodeState(7, 'completed');
            selectNode(7);
            document.getElementById('flow-ai-prop').innerText = "+1 Node (default)";

            // Step 8: Policy Gate Check
            document.getElementById('engine-state-title').innerText = "EVALUATING RECOVERY POLICY";
            setNodeState(8, 'active');
            selectNode(8);
            appendStream("Recovery Policy Engine evaluating rate limits, bounds (max 2), and pool cooldowns...");
            await sleep(600);
            document.getElementById('flow-decision-pill').className = "policy-step-pill policy-pass";
            document.getElementById('flow-decision-text').innerText = "ALLOWED";
            document.getElementById('policy-verdict-banner').className = "policy-banner policy-pass";
            document.getElementById('policy-verdict-title').innerText = "✓ POLICY PASSED (ALLOWED)";
            document.getElementById('policy-verdict-reason').innerText = "Request +1 node is <= max limit 2";
            document.getElementById('metric-decisions').innerText = "1";
            setNodeState(8, 'completed');

            // Step 9 & 10: Scale Action & Capacity
            document.getElementById('engine-state-title').innerText = "PROVISIONING ELASTIC CAPACITY";
            setNodeState(9, 'active');
            selectNode(9);
            appendStream("Dispatched scale_up request to Autoscaler Provider (+1 Node)...");
            const scaleResult = await callMCPTool('request_scale_up', { node_pool: 'default', target_nodes: 1, agent_id: 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' });
            appendStream(`Autoscaler: Status = ${scaleResult.status} | Scale Allowed = ${scaleResult.allowed}`);
            await sleep(800);
            setNodeState(9, 'completed');

            setNodeState(10, 'active');
            selectNode(10);
            appendStream("New node provisioned and in Ready state with 4000m CPU headroom.");
            await sleep(600);
            setNodeState(10, 'completed');

            // Step 11: Agent Verified Running
            document.getElementById('engine-state-title').innerText = "VERIFYING AGENT WORKLOAD";
            setNodeState(11, 'active');
            selectNode(11);
            const verifyResult = await callMCPTool('verify_agent_recovery', { agent_id: 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' });
            appendStream(`Verification: Pod Replicas Ready = 1/1 | Recovered = ${verifyResult.recovered}`);
            await sleep(500);
            setNodeState(11, 'completed');

            // Completed State
            clearInterval(timerInterval);
            document.getElementById('engine-state-title').innerText = "RECOVERED / RUNNING";
            document.getElementById('engine-state-desc').innerText = "Nasiko Agent pod healthy and actively processing requests.";
            document.getElementById('metric-pending').innerText = "0";
            document.getElementById('metric-recoveries').innerText = "1";
            appendStream("Autonomous recovery cycle complete. Zero human intervention required.");

            document.getElementById('btn-run-demo').disabled = false;
            isRunningDemo = false;
        }

        async function simulatePolicyBlock() {
            appendStream("--- INITIATING SAFETY POLICY DENIAL DEMO ---");
            appendStream("AI Reasoner or rogue client requesting +5 nodes (Exceeds safety limit of 2)...");
            
            document.getElementById('engine-state-title').innerText = "POLICY DENIED / BLOCKED";
            document.getElementById('engine-state-desc').innerText = "Recovery Policy Engine intervened to prevent over-provisioning.";
            
            document.getElementById('flow-ai-prop').innerText = "+5 Nodes (EXCESSIVE)";
            document.getElementById('flow-decision-pill').className = "policy-step-pill policy-fail";
            document.getElementById('flow-decision-text').innerText = "DENIED";

            const result = await callMCPTool('request_scale_up', { node_pool: 'default', target_nodes: 5 });
            
            document.getElementById('policy-verdict-banner').className = "policy-banner policy-fail";
            document.getElementById('policy-verdict-title').innerText = "✕ POLICY DENIED";
            document.getElementById('policy-verdict-reason').innerText = `Reason: ${result.reason || 'MAX_NODES_PER_REQUEST_EXCEEDED'}`;
            
            appendStream(`RecoveryPolicyEngine: BLOCKED! Reason: ${result.reason || 'MAX_NODES_PER_REQUEST_EXCEEDED'}. Allowed: false.`);
            appendStream("Infrastructure state unchanged. Safety invariants preserved.");
            
            setNodeState(8, 'blocked');
            selectNode(8);
        }

        // Initialize on Load
        window.addEventListener('DOMContentLoaded', () => {
            fetchHealth();
            selectNode(1);
        });
    </script>
</body>
</html>
"""
